"""LLM 统一封装：换模型、记账、重试都收在这一层。

WHY 不让 loop 直接发 HTTP：
  1. 换模型只改这里 —— 评测要在 DeepSeek / Qwen / GLM 三家之间切；
  2. 记账只改这里 —— 每次调用的 token 和钱必须落下来，否则「省了多少」说不清；
  3. 重试只改这里 —— 429/5xx 是基础设施问题，不该污染 agent 逻辑。

依赖：只用标准库 urllib，不装 requests、不装 openai sdk。
  一次 chat 往返就是一个 POST，urllib 够用，少一个依赖少一处版本地狱。
  代价：没有连接池、没有自动重试，所以下面自己写重试。
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

# 单价：元 / 百万 token。换模型时只改这张表，别把价格散落到代码里。
PRICING = {
    "deepseek-chat": {"in": 2.0, "out": 8.0},
}
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
RETRY_STATUS = {429, 500, 502, 503, 504}


class LLMError(RuntimeError):
    """LLM 层的所有失败都收敛成这一个异常。

    WHY：调用方只需要接一种异常。如果让 HTTPError、URLError、JSONDecodeError
         各自冒出来，loop 里就会长出一堆 except，而那跟 agent 逻辑一点关系没有。
    """


@dataclass
class Usage:
    """一次调用的记账。字段名和 OpenAI 兼容响应的 usage 对齐，方便直接赋值。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    cost_yuan: float = 0.0

    def __iadd__(self, other: "Usage") -> "Usage":
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.latency_s += other.latency_s
        self.cost_yuan += other.cost_yuan
        return self

    def as_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_s": round(self.latency_s, 3),
            "cost_yuan": round(self.cost_yuan, 6),
        }


@dataclass
class ChatResult:
    """一次 chat 的返回值：模型给的消息 + 这次花的钱。"""

    message: dict
    usage: Usage


class LLMClient:
    """同步、无流式、一次只做一轮往返。W1 够用。

    TRAP：别在这里加 asyncio。第一版 loop 是同步的，改成 async 会让每个调用点
          都跟着改，而你现在还看不出 async 买到了什么。等 loop 跑通、评测出来
          瓶颈在并发拉多个候选时再谈。
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise LLMError(
                "没有 API key。做法二选一：\n"
                "  1) export DEEPSEEK_API_KEY=sk-...  然后重开终端\n"
                "  2) LLMClient(api_key='sk-...')（只在本机调试时用，别提交进 git）"
            )
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.total = Usage()  # 这个 client 实例的累计账

    # ---- 内部：一次 HTTP 往返 ----
    def _post(self, payload: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---- 对外：只暴露 chat ----
    def chat(self, messages: list[dict], tools: list[dict] | None = None, temperature: float = 0.0) -> ChatResult:
        payload: dict = {"model": self.model, "messages": messages, "temperature": temperature}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        started = time.monotonic()
        data = None
        for attempt in range(self.max_retries + 1):
            try:
                data = self._post(payload)
                break
            except urllib.error.HTTPError as err:
                body = err.read().decode("utf-8", "replace")[:300]
                if err.code in RETRY_STATUS and attempt < self.max_retries:
                    time.sleep(2**attempt)  # 1s, 2s：别用固定间隔，会被限流器打回来
                    continue
                raise LLMError(f"HTTP {err.code}：{body}") from err
            except (urllib.error.URLError, TimeoutError) as err:
                if attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                raise LLMError(f"网络失败：{err}") from err
            except json.JSONDecodeError as err:
                # TRAP：网关返回 HTML 错误页时，这里才是最先炸的地方。
                raise LLMError(f"响应不是 JSON：{err}") from err

        if data is None:
            raise LLMError("重试用尽仍未拿到响应")

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        raw_usage = data.get("usage") or {}
        price = PRICING.get(self.model, {"in": 0.0, "out": 0.0})
        usage = Usage(
            prompt_tokens=int(raw_usage.get("prompt_tokens", 0)),
            completion_tokens=int(raw_usage.get("completion_tokens", 0)),
            latency_s=time.monotonic() - started,
            cost_yuan=(
                raw_usage.get("prompt_tokens", 0) / 1e6 * price["in"]
                + raw_usage.get("completion_tokens", 0) / 1e6 * price["out"]
            ),
        )
        self.total += usage
        return ChatResult(message=message, usage=usage)

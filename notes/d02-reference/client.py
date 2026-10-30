"""LLM 统一封装：换模型、记账、重试都收在这一层。

WHY 不让 loop 直接发 HTTP：
  1. 换模型只改这里 —— 评测要在 DeepSeek / Qwen / GLM 之间切；
  2. 记账只改这里 —— 每次调用的 token 和钱必须落下来，否则「省了多少」说不清；
  3. 重试只改这里 —— 429/5xx 是基础设施问题，不该污染 agent 逻辑。

依赖：只用标准库 urllib，不装 requests、不装 openai sdk。
  一次 chat 往返就是一个 POST，urllib 够用，少一个依赖少一处版本地狱。
  代价：没有连接池、没有自动重试，所以下面自己写了重试。
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from src.llm.types import (
    DEFAULT_BASE_URL, DEFAULT_MODEL, PRICING, RETRY_STATUS,
    ChatResult, LLMError, Usage,
)


class LLMClient:
    """同步、无流式、一次只做一轮往返。W1 够用。

    TRAP：别在这里加 asyncio。第一版 loop 是同步的，改成 async 会让每个调用点
          跟着改，而你现在还看不出 async 买到了什么。等 loop 跑通、评测出来
          瓶颈真的在并发时再谈。
    """

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None,
                 base_url: str | None = None, timeout: float = 60.0,
                 max_retries: int = 2) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise LLMError(
                "没有 API key。二选一：\n"
                "  1) export DEEPSEEK_API_KEY=sk-...  然后重开终端\n"
                "  2) LLMClient(api_key='sk-...')（只用于本机调试，别提交进 git）"
            )
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.total = Usage()  # 这个实例的累计账

    def _post(self, payload: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def chat(self, messages: list, tools: list | None = None,
             temperature: float = 0.0) -> ChatResult:
        payload: dict = {"model": self.model, "messages": messages,
                         "temperature": temperature}
        if tools:
            payload["tools"] = tools
            # auto = 模型自己决定调不调；"required" 会逼它每轮都调，评测「该不该调」时才有用
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
                    time.sleep(2 ** attempt)  # 1s, 2s：定时睡死间隔会被限流器反过来打
                    continue
                raise LLMError(f"HTTP {err.code}：{body}") from err
            except (urllib.error.URLError, TimeoutError) as err:
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise LLMError(f"网络失败：{err}") from err
            except json.JSONDecodeError as err:
                # TRAP：网关返回 HTML 错误页时，最先炸的是这里，不是 HTTPError。
                raise LLMError(f"响应不是 JSON：{err}") from err

        if data is None:
            raise LLMError("重试用尽仍未拿到响应")

        message = ((data.get("choices") or [{}])[0].get("message")) or {}
        raw = data.get("usage") or {}
        price = PRICING.get(self.model, {"in": 0.0, "out": 0.0})
        usage = Usage(
            prompt_tokens=int(raw.get("prompt_tokens", 0)),
            completion_tokens=int(raw.get("completion_tokens", 0)),
            latency_s=time.monotonic() - started,
            cost_yuan=(raw.get("prompt_tokens", 0) / 1e6 * price["in"]
                       + raw.get("completion_tokens", 0) / 1e6 * price["out"]),
        )
        self.total += usage
        return ChatResult(message=message, usage=usage)

"""LLM 层的数据类型与定价表。

WHY 从 client.py 拆出来：client 只该关心「怎么把一次请求发出去、怎么把结果拿回来」。
   价格表和记账结构是另一件事——换模型时你只改这张表，不用读 HTTP 代码。
"""
from __future__ import annotations

from dataclasses import dataclass

# 单价：元 / 百万 token。换模型只改这里。
PRICING = {
    "deepseek-chat": {"in": 2.0, "out": 8.0},
}
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
RETRY_STATUS = {429, 500, 502, 503, 504}


class LLMError(RuntimeError):
    """LLM 层的所有失败都收敛成这一个异常。

    WHY：调用方只需要接一种。若让 HTTPError / URLError / JSONDecodeError 各自冒出来，
         loop 里就会长出一堆 except，而那跟 agent 逻辑一点关系都没有。
    """


@dataclass
class Usage:
    """一次调用的记账。字段名与 OpenAI 兼容响应的 usage 对齐。"""

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

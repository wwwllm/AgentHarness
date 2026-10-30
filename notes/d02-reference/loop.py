"""最小 agent 主循环（同步版）。

数据流一句话：
    拼上下文 → 调模型 → 模型要么给 content（结束），要么给 tool_calls（执行并回灌）→ 再判

真正不可省的骨架就是标 `# CORE` 的那 20 来行；其余是工程外壳（trace、参数校验、异常兜底）。
第一遍只读 CORE，第二遍再问每层外壳在防什么。

运行（项目根目录）：
    export DEEPSEEK_API_KEY=sk-...
    python -m src.agent.loop "把空调调到 24 度，然后告诉我空调现在的状态"
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.tools.builtin import BUILTIN_TOOLS, Tool
from src.trace import default_path, tool_record
from src.trace import write as write_trace

SYSTEM_PROMPT = (
    "你是车载座舱助手。你可以调用工具读取车况、设置空调、查天气。\n"
    "规则：\n"
    "1. 需要真实状态时必须调工具，不要凭记忆回答。\n"
    "2. 工具返回 ok=false 时，读 error.hint 决定是重试还是问用户，不要无视。\n"
    "3. 工具结果才是事实；用户没给必要参数（比如温度数值）时先问，不要猜。"
)


@dataclass
class LoopResult:
    ok: bool
    content: str
    steps: int
    reason: str                      # done | max_steps
    usage: dict = field(default_factory=dict)
    messages: list = field(default_factory=list)


def _assistant_message(msg: dict) -> dict:
    """只挑回灌需要的字段。TRAP：别直接 append(msg)——DeepSeek 的 message 可能带
    reasoning_content 等额外字段，原样塞回去下一轮会报「不认识的字段」。白名单最稳。"""
    out = {"role": "assistant", "content": msg.get("content") or ""}
    if msg.get("tool_calls"):
        out["tool_calls"] = msg["tool_calls"]
    return out


def _run_one_call(call: dict, by_name: dict) -> tuple[dict, str, str]:
    """执行单个 tool_call → (结果, 工具名, 原始参数)。
    WHY 单独成函数：循环里再嵌三层 try，就没人看得出 CORE 在哪了。"""
    fn = call.get("function") or {}
    name = fn.get("name", "")
    raw_args = fn.get("arguments") or "{}"
    try:
        args = json.loads(raw_args)
        if not isinstance(args, dict):
            raise ValueError("arguments 不是 JSON 对象")
    except (json.JSONDecodeError, ValueError) as err:
        return ({"ok": False, "error": {
            "code": "BAD_ARGUMENTS", "message": str(err),
            "hint": "重新调用一次，arguments 必须是合法 JSON 对象"}}, name, raw_args)
    tool = by_name.get(name)
    if tool is None:
        return ({"ok": False, "error": {
            "code": "UNKNOWN_TOOL", "message": f"没有工具 {name}",
            "hint": f"可用工具：{list(by_name)}"}}, name, raw_args)
    try:
        out = tool.handler(args)
    except Exception as err:          # 工具不守规矩时也别炸穿整个 loop
        out = {"ok": False, "error": {"code": "TOOL_CRASHED", "message": repr(err),
                                      "hint": "工具内部异常，换参数重试或放弃这个意图"}}
    if not isinstance(out, dict):     # 返回 None 是第二类错，别等到回灌才炸
        out = {"ok": False, "error": {"code": "BAD_RETURN", "message": f"工具返回 {type(out).__name__}",
                                      "hint": "工具必须返回 dict，形如 {'ok': True, 'data': ...}"}}
    return out, name, raw_args


def run_loop(client, instruction: str, tools: list | None = None, max_steps: int = 6,
             trace_path: Path | None = None, verbose: bool = True) -> LoopResult:
    tools = tools if tools is not None else BUILTIN_TOOLS
    by_name = {t.name: t for t in tools}
    schemas = [t.schema() for t in tools]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": instruction},
    ]

    for step in range(1, max_steps + 1):
        result = client.chat(messages, tools=schemas)             # CORE 1 调模型
        msg = result.message
        tool_calls = msg.get("tool_calls")
        messages.append(_assistant_message(msg))

        if not tool_calls:                                        # CORE 2 停止条件
            if verbose:
                print(f"[step {step}] 结束：没有 tool_calls")
            return LoopResult(ok=True, content=msg.get("content") or "", steps=step,
                              reason="done", usage=client.total.as_dict(), messages=messages)

        for call in tool_calls:                                   # CORE 3 逐个执行
            t0 = time.monotonic()
            tool_result, name, raw_args = _run_one_call(call, by_name)   # CORE 4 执行
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            if verbose:
                flag = "ok " if tool_result.get("ok") else "ERR"
                print(f"[step {step}] {flag} {name}({raw_args}) -> "
                      f"{json.dumps(tool_result, ensure_ascii=False)[:120]}")
            write_trace(trace_path, tool_record(step, name, raw_args, tool_result,
                                                elapsed_ms, getattr(client, "model", "?")))
            messages.append({                                     # CORE 5 回灌
                "role": "tool",
                "tool_call_id": call.get("id", ""),
                "content": json.dumps(tool_result, ensure_ascii=False),
            })

    return LoopResult(ok=False, content="", steps=max_steps, reason="max_steps",
                      usage=client.total.as_dict(), messages=messages)


def main() -> int:
    from src.llm.client import LLMClient  # 延迟 import：只测 loop 时不必带 client
    from src.llm.types import LLMError

    instruction = " ".join(sys.argv[1:]).strip() or "把空调调到 24 度，然后告诉我空调现在的状态"
    try:
        client = LLMClient()
    except LLMError as err:
        print(f"启动失败：{err}", file=sys.stderr)
        return 2

    trace_path = default_path()
    result = run_loop(client, instruction, trace_path=trace_path)
    print("\n--- 结果 ---")
    print(f"reason={result.reason} steps={result.steps} usage={result.usage}")
    print(f"模型最后说：{result.content or '（空）'}")
    print(f"trace: {trace_path}")
    return 0 if result.reason == "done" else 1


if __name__ == "__main__":
    raise SystemExit(main())

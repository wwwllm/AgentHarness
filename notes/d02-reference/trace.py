"""一次工具调用写一行 JSONL。

WHY 单独一个文件，不内联在 loop 里：
  trace 是横向能力——网关、评测脚本、回放工具都要读它，不该长在主循环身上。
  塞在 loop 里会让一个 90 行能读懂的函数多出 20 行与本职无关的噪音。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

TRACE_DIR = Path("traces")


def default_path() -> Path:
    """当天一个文件。按天切分是为了「昨天那轮为什么慢」能直接翻到。"""
    return TRACE_DIR / f"{datetime.now():%Y%m%d}.jsonl"


def tool_record(step: int, tool: str, args_raw: str, result: dict,
                elapsed_ms: int, model: str) -> dict:
    """字段固定成一张表，不要每次随手加。

    WHY：回放和统计靠字段名对齐；随手加字段，三个月后自己都记不住有哪些。
         要加字段就走这里，一处加、全链路可见。
    """
    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "step": step,
        "tool": tool,
        "args_raw": args_raw,
        "ok": bool(result.get("ok")),
        "result": result,
        "elapsed_ms": elapsed_ms,
        "model": model,
    }


def write(path: Path | None, record: dict) -> None:
    """写失败绝不能中断 agent。

    WHY：trace 是观测手段，不是业务逻辑。磁盘满了、权限错了，
         赔上整个任务不划算——打一行 stderr 继续跑。
    """
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as err:
        print(f"[trace] 写失败（已忽略）：{err}", file=sys.stderr)

"""工具定义：schema（给模型看）和 handler（我这边执行）绑成一个对象。

WHY 不用装饰器自动注册：
  两个工具时 @register 很优雅，到 20 个工具时你就看不出「到底有哪些工具、在哪注册、
  顺序如何」。显式写进 BUILTIN_TOOLS 列表，一屏看完。装饰器留到真需要横切逻辑时再上。

WHY schema 和 handler 必须绑在一起：
  它们是最容易漂移的一对——schema 里漏一个参数，模型就永远不会传；
  handler 多要一个参数，模型每次调用都会缺参。绑在一起，改一边就看得见另一边。

description 的写法（AGENTS.md §5）：做什么 + 什么时候不该用 + 参数含义。
  只写「设置空调温度」是不够的——模型不知道「调高一点」算不算能调。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

# 车况真对象。W1 先用 dict 顶替，W5 换成 sim/vehicle_sim.cpp 通过 stdin 通信。
# TRAP：工具只许改这里的键，不许重新绑定名字（state = {...}）。
STATE: dict[str, Any] = {"ac_temp": 26, "ac_on": False, "speed_kmh": 0}


def _err(code: str, msg: str, hint: str) -> dict:
    """统一错误结构。hint 是给模型看的修复提示，不是给人看的日志。"""
    return {"ok": False, "error": {"code": code, "message": msg, "hint": hint}}


def control_ac(args: dict) -> dict:
    temp = args.get("temperature")
    if isinstance(temp, bool) or not isinstance(temp, int):
        return _err("BAD_TYPE", f"temperature 必须是整数，收到 {temp!r}", "例如 {\"temperature\": 24}")
    if not 16 <= temp <= 30:
        return _err("OUT_OF_RANGE", f"温度 {temp} 超出 16~30", "请给 16 到 30 之间的整数；用户没给数值就先问")
    STATE["ac_temp"] = temp
    STATE["ac_on"] = True
    return {"ok": True, "data": {"ac_temp": temp, "ac_on": True}}


def get_weather(args: dict) -> dict:
    city = args.get("city")
    if not isinstance(city, str) or not city.strip():
        return _err("MISSING_ARG", "缺少参数 city", "例如 {\"city\": \"重庆\"}")
    # WHY 返回假数据：W1 的目标是链路，不是数据源。接真天气 API 是 W3 的事。
    return {"ok": True, "data": {"city": city, "text": "多云", "temp_c": 22}, "mock": True}


def get_vehicle_status(args: dict) -> dict:
    return {"ok": True, "data": dict(STATE)}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable[[dict], dict]

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


BUILTIN_TOOLS: list[Tool] = [
    Tool(
        name="control_ac",
        description=(
            "设置车内空调的目标温度并开启空调，返回设置后的状态。"
            "仅当用户明确给出一个 16~30 摄氏度之间的目标温度时调用；"
            "用户只说「调高一点」「凉一点」而没有数值时不要猜，先问清楚。"
            "不要用它关空调或调风量——这个工具只处理温度。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "temperature": {
                    "type": "integer",
                    "minimum": 16,
                    "maximum": 30,
                    "description": "目标温度，摄氏度整数，取值范围 16~30",
                }
            },
            "required": ["temperature"],
        },
        handler=control_ac,
    ),
    Tool(
        name="get_weather",
        description=(
            "查询指定城市的实时天气（气温 + 天况）。"
            "仅在用户问天气、出行穿着、要不要开空调这类外部信息时调用；"
            "车速、油量、空调温度属于车况，用 get_vehicle_status，不要用这个。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "中文城市名，如「重庆」"}
            },
            "required": ["city"],
        },
        handler=get_weather,
    ),
    Tool(
        name="get_vehicle_status",
        description=(
            "读取当前车况：车速、空调开关、空调目标温度。"
            "在执行任何改动类操作之前、或用户问「现在多少度」时调用，用来确认真实状态。"
            "它只读，不会改变任何东西。"
        ),
        parameters={"type": "object", "properties": {}},
        handler=get_vehicle_status,
    ),
]

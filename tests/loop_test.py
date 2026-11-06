import types
from src.agent.loop import run, AC_STATUS, TOOL_LOG

class FakeClient:
    def __init__(self,script):
        self.script=script
        self.calls=0
        self.chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))
    def _create(self, **kwargs):
        if self.calls >= len(self.script):
            raise RuntimeError(f"剧本只有 {len(self.script)} 幕，第 {self.calls + 1} 次调用没内容")
        turn = self.script[self.calls]
        self.calls += 1                      
        if "tool" in turn:
            call = types.SimpleNamespace(
                id=f"call_{self.calls}",
                function=types.SimpleNamespace(name=turn["tool"], arguments=turn["args"]),
            )
            message = types.SimpleNamespace(content=None, tool_calls=[call])
        else:
            message = types.SimpleNamespace(content=turn["final"], tool_calls=None)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])

CASES = [
    ("1 正常", "把空调调到 24 度", [
        {"tool": "control_ac", "args": '{"temp": 24}'},
        {"final": "已把空调调到 24 度"},
    ]),
    ("2 越界", "把空调调到 99 度", [
        {"tool": "control_ac", "args": '{"temp": 99}'},
        {"final": "99 度超出 16-30 的范围，我没改"},
    ]),
    ("3 未知工具", "把车窗打开 30%", [
        {"tool": "control_window", "args": '{"percent": 30}'},
        {"final": "我没有控制车窗的能力"},
    ]),
    ("4 坏 JSON", "把空调调到 24 度", [
        {"tool": "control_ac", "args": '{"temp": 24'},
        {"final": "参数格式不对，请重试"},
    ]),
]
if __name__ == "__main__":
    for label, cmd, script in CASES:
        AC_STATUS["temp"] = 27          
        TOOL_LOG.clear()
        print(f"\n===== {label} =====")
        print("指令     :", cmd)
        print("模型说   :", run(cmd, client=FakeClient(script)))
        for item in TOOL_LOG:
            print("工具执行 :", item["tool"], item["args"], "→", item["res"])
        print("真实状态 :", AC_STATUS)
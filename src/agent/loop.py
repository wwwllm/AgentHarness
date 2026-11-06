import json
import os
from openai import OpenAI

AC_STATUS={"temp":27}
def get_weather(city:str)->dict:
    if not city:
        return {"ok":False,"error":"city参数缺失"}
    return {"ok":True,"data":{"city":city,"weather":"晴天"}}

def control_ac(temp:int)->dict:
    if temp is None:
        return {"ok":False,"error":"temp参数缺失"}
    if isinstance(temp, bool) or not isinstance(temp, (int, float)):
        return {"ok":False,"error":"temp 必须是数字"}
    if temp>30 or temp < 16:
        return {"ok":False,"error":"temp参数必须在16-30之间"}
    AC_STATUS["temp"]=temp
    return {"ok":True,"data":{"temp":temp,"status":"空调已设置"}}

tools=[
    {
        "type":"function",
        "function":{
            "name":"get_weather",
            "description":"获取天气",
            "parameters":{
                "type":"object",
                "properties":{
                    "city":{
                        "type":"string",
                        "description":"城市名称"
                    },
                },
                "required":["city"]
            },
        },
    },
    {
        "type":"function",
        "function":{
            "name":"control_ac",
            "description":"控制空调温度",
            "parameters":{
                "type":"object",
                "properties":{
                    "temp":{
                        "type":"number",
                        "description":"温度值，范围16-30"
                    }
                },
                "required":["temp"]
            },
        },
    },
]
TOOL_MAP = {
    "get_weather": get_weather,
    "control_ac": control_ac
}
TOOL_LOG=[]
def invoke_tool(tool_call)->dict:
    name=tool_call.function.name
    raw_args=tool_call.function.arguments
    fun=TOOL_MAP.get(name)
    if fun is None:
        err=f"工具 {name} 不存在，可用工具：{', '.join(TOOL_MAP)}"
        TOOL_LOG.append({"tool":name,"args":raw_args,"res":{"ok":False,"error":err}})
        return {"ok":False,"error":err}
    try:
        args=json.loads(raw_args)
    except json.JSONDecodeError as e:
        err=f"参数不是合法 JSON: {e}"
        TOOL_LOG.append({"tool":name,"args":raw_args,"res":{"ok":False,"error":err}})
        return {"ok":False,"error":err}

    if not isinstance(args, dict):
        err=f"参数必须是 JSON 对象，收到 {type(args).__name__}"
        TOOL_LOG.append({"tool":name,"args":raw_args,"res":{"ok":False,"error":err}})
        return {"ok":False,"error":err}

    try:
        res=fun(**args)
        TOOL_LOG.append({"tool":name,"args":raw_args,"res":res})
        return res
    except TypeError as e:
        err=f"工具 {name} 的参数不匹配: {e}"
        TOOL_LOG.append({"tool":name,"args":raw_args,"res":{"ok":False,"error":err}})
        return {"ok":False,"error":err}


def run(command: str,max_steps:int=3,client=None)->str:
    if client is None:
        client=OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=  os.getenv("DEEPSEEK_API_URL")
        )
    
    messages=[{"role":"user","content":command}]
    sub_turn=1
    while True:
        response=client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            tools=tools,
            reasoning_effort="medium",
            extra_body={"thinking":
                {"type":"enabled"}
            },
        )
        messages.append(response.choices[0].message)
        if response.choices[0].message.tool_calls is None:
            break
        for tool in response.choices[0].message.tool_calls:
            tool_res=invoke_tool(tool)
            messages.append({
                "role":"tool",
                "name":tool.function.name,
                "tool_call_id":tool.id,
                "content":json.dumps(tool_res,ensure_ascii=False)
            })
        sub_turn+=1
        if sub_turn>max_steps:
            return "超过最大步数限制"
    return messages[-1].content


if __name__ == "__main__":
    for cmd in ["把空调调到 24 度","把空调调到 99 度","把车窗打开 30%"]:
        AC_STATUS["temp"] = 27          
        TOOL_LOG.clear()
        print(f"\n======================")
        print("指令     :", cmd)
        print("模型说   :", run(cmd))
        for item in TOOL_LOG:
            print("工具执行 :", item["tool"], item["args"], "→", item["res"])
        print("真实状态 :", AC_STATUS)
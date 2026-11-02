import re
import json
import os
from openai import OpenAI

AC_STATUS={"temp":27}
client=OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_URL")
)
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

def run(command: str,max_steps:int=3)->str:
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
            tool_fun=TOOL_MAP[tool.function.name]
            tool_res=tool_fun(**json.loads(tool.function.arguments))
            messages.append({
                "role":"tool",
                "name":tool.function.name,
                "tool_call_id":tool.id,
                "content":json.dumps(tool_res)
            })
        sub_turn+=1
        if sub_turn>max_steps:
            return "超过最大步数限制"
    return messages[-1].content


if __name__ == '__main__':
    for ins in ["把空调调到 24 度", "把空调调到 -16 度", "把空调调到 99 度"]:
            print("指令:", ins)
            print("  模型说:", run(ins))
            print("  真实状态:", AC_STATUS)  
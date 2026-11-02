import re
import json

AC_STATUS={"temp":27};
def get_weather(argvs:dict)->dict:
    city=argvs.get("city")
    if not city:
        return {"ok":False,"error":"city参数缺失"}
    return {"ok":True,"data":{"city":city,"weather":"晴天"}}


def control_ac(argvs:dict)->dict:
    temp=argvs.get("temp")
    if temp is None:
        return {"ok":False,"error":"temp参数缺失"}
    if isinstance(temp, bool) or not isinstance(temp, (int, float)):
        return {"ok":False,"error":"temp 必须是数字"}
    if temp>30 or temp < 16:
        return {"ok":False,"error":"temp参数必须在16-30之间"}
    AC_STATUS["temp"]=temp
    return {"ok":True,"data":{"temp":temp,"status":"空调已设置"}}

TOOL_REGISTRY={"get_weather":get_weather,"control_ac":control_ac}
def invoke(messages:list)->dict:
    if any(m["role"]=="tool" for  m in messages):
        temp = re.search(r"-?\d+", messages[0]["content"])
        return {"content":f"已经将空调温度设置为{temp.group()}度"}
    temp = re.search(r"-?\d+", messages[0]["content"])
    if temp is None:                      
        return {"content": "我没听出你要设置的温度，请说一个 16~30 的数字。"}
    if int(temp.group())>30 or int(temp.group()) < 16:
            return {"ok":False,"error":"temp参数必须在16-30之间"}
    argvs ={"temperature":int(temp.group())} if temp else {}
    return {"tool_calls":[{"id":"call_1","function":{"name":"control_ac","arguments":json.dumps(argvs)}} ]}
    

def run(command:str ,max_steps:int=3)->None:
    messages=[{"role":"user","content":command}]
    for step in range(1,max_steps+1):
        resp=invoke(messages)
        tool_calls=resp.get("tool_calls")
        if tool_calls:
            messages.append({"role":"assisant","tool_calls":tool_calls})
            for tc in tool_calls:
                func_name=tc["function"]["name"]
                try:
                    args=json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    res={"ok":False,"error":"参数解析失败"}
                else:
                    fn=TOOL_REGISTRY.get(func_name)
                    if fn is None:
                        res={"ok":False,"error":f"函数{func_name}未注册"}
                    else: 
                        res=fn(args)
                        if not isinstance(res,dict):
                            res = {"ok": False, "error": "工具没返回 dict", "hint": "统一 {ok,...}"}
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": json.dumps(res, ensure_ascii=False)}) 
        else:
            return resp.get("content")
    return "对话轮数超过最大限制，终止对话。"

if __name__ == '__main__':
    for ins in ["把空调调到 24 度", "把空调调到 -16 度", "把空调调到 99 度"]:
            print("指令:", ins)
            print("  模型说:", run(ins))
            print("  真实状态:", AC_STATUS)  
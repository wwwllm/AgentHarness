
def get_weather():pass
def control_ac():pass
TOOL_REGISTRY={"get_weather":get_weather,"control_ac":control_ac}
def invoke(prompt:str|dict)->tuple[str, dict]:
    # Placeholder implementation
    return "get_weather", {}
def run(command:str ,max_steps:int=3)->None:
    for step in range(1,max_steps+1):
        try:
            fun_name,argvs=invoke(command)
        except OSError as err:
            print("OS Error: ",err)
        TOOL_REGISTRY[fun_name](argvs)

if __name__ == '__main__':
    run("今天吃什么？")
    run("把空调温度调到-273度。")
    run("把空调温度调到16度。")
import os
import json

from typing import Optional, Dict, Callable

class FunctionDescription:
    """
    函数描述类，包含函数的描述信息、参数和返回值信息
    add_parameter 方法用于添加参数
    add_return 方法用于添加返回值
    to_schema 方法用于将函数描述转换为 function calling 所需的格式
    """

    def __init__(self, name: str, description: str):
        """
        参数：
            name: 函数名称
            description: 函数描述
        说明：
            默认没有参数和返回值
        """

        self.name = name
        self.description = description
        self.parameters = {}
        self.return_value = None

    def add_parameter(self, name: str, param_type: str, description: str, required: bool = False) -> "FunctionDescription":
        """
        添加参数，参数：
            name: 参数名称
            param_type: 参数类型
            description: 参数描述
            required: 是否必需
        返回值：
            返回函数描述对象本身，支持链式调用
        """
        self.parameters[name] = {
            "type": param_type,
            "description": description,
            "required": required
        }
        return self
    
    def add_return(self, name: str, description: str) -> None:
        """
        添加返回值，其类型为 str，参数：
            name: 返回值名称
            description: 返回值描述
        """
        self.return_value = {
            "name": name,
            "description": description
        }

    def to_schema(self) -> dict:
        """
        将当前函数描述转换为 function calling 所需的格式
        """
        props = {}
        required_list = []

        # 遍历参数
        for name, info in self.parameters.items():
            props[name] = {
                "type": info["type"],
                "description": info["description"]
            }
            if info.get("required"):
                required_list.append(name)

        # 构建最终 schema
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": props,
            }
        }

        # 只在有 required 时加入 required 字段
        if required_list:
            schema["parameters"]["required"] = required_list

        return schema


class FunctionContainer:
    """
    全局唯一的函数调用管理容器，用于注册和存储所有可用的函数
    """

    def __init__(self, path: Optional[str] = None):
        """
        参数：
            path: 函数文件路径，默认为 None，表示使用当前文件所在目录下的 'function_calling' 文件夹
        """

        self.functions: Dict[str, Callable] = {}
        self.function_descriptions: Dict[str, FunctionDescription] = {}

        if path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(current_dir, 'function_calling')
        self.path = path
    
    def function_calling(self, function_description: FunctionDescription) -> Callable:
        """
        注册 function calling 函数
        """

        def decorator(func: Callable):
            self.functions[function_description.name] = func
            self.function_descriptions[function_description.name] = function_description
            return func

        return decorator
    
    def load_functions(self) -> None:
        """
        从指定路径加载所有注册的函数
        """

        # todo: 实现从文件加载函数的逻辑
        pass


class FunctionCalling:
    """
    为每个不同的聊天上下文使用的函数调用管理器
    call 方法用于调用函数
    to_schemas 方法用于获取所有函数的 Function Calling 描述
    """

    def __init__(self, group_id: int, function_container: FunctionContainer):
        """
        参数：
            group_id: 组ID
        """

        self.group_id = group_id
        self.functions: Dict[str, Callable] = function_container.functions
        self.function_descriptions: Dict[str, FunctionDescription] = function_container.function_descriptions
    
    def call(self, name: str, args: dict) -> Optional[str]:
        """
        调用函数

        参数：
            name: 函数名称
            args: 函数参数

        返回：
            dict: 函数调用结果
        """
        if name not in self.functions:
            return f"函数 {name} 不存在"
        try:
            return self.functions[name](**args)
        except Exception as e:
            return f"函数调用出错: {e}"
        
    def to_schemas(self) -> str:
        """
        获取所有函数的 Function Calling 描述
        """
        functions =  [
            fd.to_schema()
            for fd in self.function_descriptions.values()
        ]
        return json.dumps(functions, ensure_ascii=False, indent=2)


# 全局唯一的函数容器实例
function_container = FunctionContainer()
# 加载所有注册的函数
function_container.load_functions()

if __name__ == "__main__":
    func_desc_add = FunctionDescription(name="add", description="Add two numbers")
    func_desc_add.add_parameter(name="a", param_type="number", description="First number", required=True)
    func_desc_add.add_parameter(name="b", param_type="number", description="Second number", required=True)
    func_desc_add.add_return(name="result", description="The sum of a and b")

    @function_container.function_calling(func_desc_add)
    def add(a: float, b: float) -> str:
        return str(a + b)
    
    func_desc_time = FunctionDescription(name="get_current_time", description="Get the current system time")
    func_desc_time.add_return(name="current_time", description="The current system time as a string")

    @function_container.function_calling(func_desc_time)
    def get_current_time() -> str:
        from datetime import datetime
        return datetime.now().isoformat()

    function_calling = FunctionCalling(group_id=1, function_container=function_container)

    result = function_calling.call("add", {"a": 5, "b": 3})
    print(f"Function call result: {result}")  # 输出: Function call result: 8.0

    result = function_calling.call("get_current_time", {})
    print(f"Function call result: {result}")  # 输出现在的时间

    print("Function schemas:")
    print(function_calling.to_schemas())

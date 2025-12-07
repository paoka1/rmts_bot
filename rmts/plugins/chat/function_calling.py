import os
import json
import asyncio

from pathlib import Path
from importlib import import_module
from typing import Optional, Dict, Callable

from nonebot.log import logger

class FunctionDescription:
    """
    函数描述类，包含函数的描述信息、参数和返回值信息
    add_parameter 方法用于添加参数
    add_injection_parameter 方法用于添加注入参数
    add_return 方法用于添加返回值
    to_schema 方法用于将函数描述转换为 function calling 所需的格式
    """

    def __init__(self, name: str, description: str):
        """
        参数：
            name: 函数名称
            description: 函数描述
        说明：
            注册的函数必须要有字符串类型的返回值，但参数没有此要求
        """

        self.name = name
        self.description = description
        self.parameters = {}
        self.injection_parameters = {}
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
    
    def add_injection_parameter(self, name: str, description: str) -> "FunctionDescription":
        """
        添加注入参数，参数：
            name: 参数名称
            description: 参数描述
        返回值：
            返回函数描述对象本身，支持链式调用
        说明：
            此方法用于在function calling中添加不需要用户提供的参数，如果响应中提供了这些参数，则不会被覆盖
            参数注入使用变量名进行匹配，这些参数由 FunctionCalling 提供
        """
        self.injection_parameters[name] = {
            "description": description
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
        
        # 构建参数 schema
        parameters_schema = {
            "type": "object",
            "properties": props,
        }
        if required_list:
            parameters_schema["required"] = required_list
        
        # 构建完整的工具 schema（包含 type 字段）
        schema = {
            "type": "function",  # ← 添加这个
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters_schema
            }
        }
        return schema


class FunctionContainer:
    """
    全局唯一的函数调用管理容器，用于注册和存储所有可用的函数
    """

    def __init__(self, path: str = "functions"):
        """
        参数：
            path: 存放函数的路径，默认为 "functions"
        说明：
            此路径应位于本文件所在目录下
        """

        self.path = path
        self.excluded_paths = ["__pycache__"]
        self.functions: Dict[str, Callable] = {}
        self.function_descriptions: Dict[str, FunctionDescription] = {}

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.fullpath = os.path.join(current_dir, Path(self.path))

        logger.info(f"从{self.fullpath}加载function calling函数")
    
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

        for dir in Path(self.fullpath).iterdir():
            if dir.is_dir() and dir.name not in self.excluded_paths:
                module_path = f"{__package__}.{self.path}.{dir.name}"
                logger.info(f"正在加载函数模块: {module_path}")
                import_module(module_path)

        logger.info("function calling 函数加载完成")
        function_names = [self.function_descriptions[name].name for name in self.function_descriptions]
        logger.info(f"已完成以下函数的加载注册：{function_names}")

class FunctionCalling:
    """
    为每个不同的聊天上下文使用的函数调用管理器
    call 方法用于调用函数
    to_schemas 方法用于获取所有函数的 Function Calling 描述
    """

    def __init__(self, function_container: FunctionContainer, injection_params: Dict[str, str] = {}):
        """
        参数：
            function_container: 全局唯一的函数容器实例
            injection_params: 全局注入参数，名称: 值
        """

        self.functions: Dict[str, Callable] = function_container.functions
        self.function_descriptions: Dict[str, FunctionDescription] = function_container.function_descriptions
        self.injection_params: Dict[str, str] = injection_params
    
    async def call(self, name: str, args: dict) -> Optional[str]:
        """
        调用函数

        参数：
            name: 函数名称
            args: 函数参数

        返回：
            str: 函数调用结果
        """
        if name not in self.functions:
            return f"函数 {name} 不存在"
        
        # 注入参数
        fd = self.function_descriptions[name]
        for inj_name in fd.injection_parameters:
            if inj_name not in args: # 注入那些没有被提供的参数
                args[inj_name] = self.injection_params[inj_name]

        logger.info(f"调用函数 {name}，参数: {args}")
        
        func = self.functions[name]
        try:
            # 检测是否为协程函数
            if asyncio.iscoroutinefunction(func):
                return await func(**args)
            else:
                return func(**args)
        except Exception as e:
            return f"函数调用出错: {e}"
        
    def to_schemas_str(self) -> str:
        """
        获取所有函数的 Function Calling 描述
        """
        functions =  [
            fd.to_schema()
            for fd in self.function_descriptions.values()
        ]
        return json.dumps(functions, ensure_ascii=False, indent=2)
    
    def to_schemas(self) -> list:
        """
        获取所有函数的 Function Calling 描述
        """
        return [
            fd.to_schema()
            for fd in self.function_descriptions.values()
        ]


# 全局唯一的函数容器实例
function_container = FunctionContainer()
# 加载所有注册的函数
function_container.load_functions()

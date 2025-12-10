import os
import json
import asyncio

from pathlib import Path
from importlib import import_module
from typing import Dict, Callable, List
from typing import Literal, TypeVar, Union, Coroutine, Any

from nonebot.log import logger

# 函数类型变量，返回值为 str 或 协程，协程返回 str
F = TypeVar('F', bound=Callable[..., Union[str, Coroutine[Any, Any, str]]])

class FunctionDescription:
    """
    函数描述类，包含函数的描述信息、参数和返回值信息
    add_str_parameter 方法用于添加字符串参数
    add_enum_parameter 方法用于添加枚举参数
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
        self.str_parameters = {}
        self.enum_parameters = {}
        self.injection_parameters = {}
        self.return_value = None

    def add_str_parameter(self, name: str, description: str, required: bool = False) -> "FunctionDescription":
        """
        添加参数，参数：
            name: 参数名称
            param_type: 参数类型
            description: 参数描述
            required: 是否必需
        返回值：
            返回函数描述对象本身，支持链式调用
        """
        self.str_parameters[name] = {
            "type": "string",
            "description": description,
            "required": required
        }
        return self
    
    def add_enum_parameter(self, name: str, description: str, enum_values: List[str], required: bool = False) -> "FunctionDescription":
        """
        添加枚举参数，参数：
            name: 参数名称
            description: 参数描述
            enum_values: 枚举值列表
            required: 是否必需
        """
        self.enum_parameters[name] = {
            "type": "string",
            "description": description,
            "enum": enum_values,
            "required": required
        }
        return self
    
    def add_injection_parameter(self, name: Literal["group_id"], description: str) -> "FunctionDescription":
        """
        添加注入参数，参数：
            name: 参数名称
            description: 参数描述
        返回值：
            返回函数描述对象本身，支持链式调用
        说明：
            此方法用于在 function calling 函数中注入不需要 LLM 提供的参数，如果 LLM 提供了这些参数，则不会覆盖
            参数注入使用变量名进行匹配，这些参数由 FunctionCalling 类提供，如果想添加更多注入参数，请修改 ModelPool 类的注入参数字典
            然后修改此方法的 name 参数类型提示，在其中添加新的参数名称
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
        
        # 遍历字符串参数
        for name, info in self.str_parameters.items():
            props[name] = {
                "type": info["type"],
                "description": info["description"]
            }
            if info.get("required"):
                required_list.append(name)
        
        # 遍历枚举参数
        for name, info in self.enum_parameters.items():
            props[name] = {
                "type": info["type"],
                "description": info["description"],
                "enum": info["enum"]
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
            "type": "function",
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
    
    def function_calling(self, function_description: FunctionDescription) -> Callable[[F], F]:
        """
        注册 function calling 函数
        """

        def decorator(func: F) -> F:
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
                module_name = f"{__package__}.{self.path}.{dir.name}" # 例如: rmts.plugins.chat.functions.action
                logger.info(f"正在加载函数模块: {module_name}")
                import_module(module_name) # 运行该文件夹下 __init__.py 中所有的 function_container.function_calling(func_desc_xxx)

        logger.success("function calling 函数加载完成")
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

        # debug 使用
        # logger.info(f"function tools str: \n{self.to_schemas_str()}\n")
    
    async def call(self, name: str, args: dict) -> str:
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
                retv = await func(**args)
            else:
                retv = func(**args)

            # 没有返回值
            if retv is None:
                logger.warning(f"函数 {name} ，参数 {args} 没有返回值，已自动转换为字符串提示")
                return "该 function calling 函数没有返回值"
            
            # 返回值不是字符串
            if not isinstance(retv, str):
                logger.warning(f"函数 {name} ，参数 {args} 返回值不是字符串，已自动转换为字符串")
                return str(retv)
            
            return retv
        except Exception as e:
            logger.exception(f"函数 {name} 调用出错，参数: {args}")
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

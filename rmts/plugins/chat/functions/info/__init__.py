"""
和获取信息有关的函数调用功能
"""

from datetime import datetime
from rmts.plugins.chat.function_calling import FunctionDescription, function_container

# 获取当前时间
func_desc_time = FunctionDescription(name="get_current_time", description="获取当前时间")

@function_container.function_calling(func_desc_time)
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

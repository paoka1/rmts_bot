"""
和获取信息有关的函数调用功能
"""

from rmts.plugins.chat.function_calling import FunctionDescription, function_container

# 获取当前时间
func_desc_time = FunctionDescription(name="get_current_time", description="获取当前系统时间")
func_desc_time.add_return(name="current_time", description="当前系统时间的字符串表示")

@function_container.function_calling(func_desc_time)
def get_current_time() -> str:
    from datetime import datetime
    return datetime.now().isoformat()

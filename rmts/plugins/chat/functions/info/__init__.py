"""
和获取信息有关的函数调用功能
"""

from datetime import datetime

from rmts.plugins.chat.function_calling import FunctionDescription, function_container

from .birthday import Birthday

# 获取当前时间
func_desc_time = FunctionDescription(name="get_current_time", description="获取当前时间")

@function_container.function_calling(func_desc_time)
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 通过日期获取过生日的干员
birthday_query = Birthday()

func_desc_birthday_by_date = FunctionDescription(name="get_birth_by_date", description="通过日期获取过生日的干员")
func_desc_birthday_by_date.add_param(name="date", description="日期字符串，格式为MM月DD日，例如1月1日", param_type="string", required=True)

@function_container.function_calling(func_desc_birthday_by_date)
def get_birth_by_date(date: str) -> str:
    result = birthday_query.get_birth_by_date(date)
    if result:
        return f"{date}过生日的干员有: {', '.join(result)}"
    else:
        return f"{date}没有干员过生日"

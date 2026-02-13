"""
和获取信息有关的函数调用功能
"""

from datetime import datetime
from typing import Optional

from nonebot import get_driver
from nonebot.log import logger

from rmts.plugins.chat.function_calling import FunctionDescription, function_container

from .birthday import Birthday
from .weather import Weather
from .operators import OperatorInfoManager
from .image_vision import ImageVision

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
    
# 通过名字获取干员的生日
func_desc_birthday_by_name = FunctionDescription(name="get_birth_by_name", description="通过名字获取干员的生日")
func_desc_birthday_by_name.add_param(name="name", description="干员名字", param_type="string", required=True)

@function_container.function_calling(func_desc_birthday_by_name)
def get_birth_by_name(name: str) -> str:
    result = birthday_query.get_birth_by_name(name)
    if result:
        return f"{name}的生日是: {result}"
    else:
        return f"没有找到名为{name}的干员的生日信息"

# 天气查询
weather_query = Weather(get_driver().config.amap_weather_api_key)

func_desc_weather = FunctionDescription(name="get_weather", description="获取天气信息")
func_desc_weather.add_param(name="location", description="查询天气的地点，如：广州市、广宁县等", param_type="string", required=True)

@function_container.function_calling(func_desc_weather)
async def get_weather(location: str) -> str:
    try:
        result = await weather_query.get_forecast_weather(location)
    except Exception as e:
        logger.error(f"获取天气信息时发生错误: {str(e)}")
        return f"获取天气信息时发生错误: {str(e)}"
    
    if result:
        return result.to_readable_text()
    else:
        return f"没有找到{location}的天气信息"

# 干员信息查询
operator_manager = OperatorInfoManager()

func_desc_operator_info = FunctionDescription(name="get_operator_info", description="获取干员信息")
func_desc_operator_info.add_param(name="name", description="干员名字，如：澄闪", param_type="string", required=True)

@function_container.function_calling(func_desc_operator_info)
async def get_operator_info(name: str) -> str:
    try:
        operator = await operator_manager.get_operator_info_by_name(name)
    except Exception as e:
        logger.error(f"获取干员信息时发生错误: {str(e)}")
        return f"获取干员信息时发生错误: {str(e)}"

    if operator:
        summary = operator.get("summary", "该干员无信息")
        return f"{name}的干员信息：{summary}"
    else:
        return f"没有找到名为{name}的干员信息"

# 图片识别
iv = ImageVision(
    api_key=get_driver().config.image_vision_api_key,
    model=get_driver().config.image_vision_model,
    base_url=get_driver().config.image_vision_base_url
)

image_vision_desc = FunctionDescription(name="analyze_image", description="分析图片并返回描述信息")
image_vision_desc.add_param(name="image_url", description="图片的URL地址", param_type="string", required=True)
image_vision_desc.add_param(name="focus_point", description="图片中需要关注的点（可选）", param_type="string", required=False)

@function_container.function_calling(image_vision_desc)
async def analyze_image(image_url: str, focus_point: Optional[str] = None) -> str:
    # 验证URL格式
    if not image_url.startswith("https://multimedia.nt.qq.com.cn/download?appid="):
        return "不支持分析该图片"
    
    try:
        result = await iv.analyze_image(image_url=image_url, focus_point=focus_point, detail="auto")
        return result
    except Exception as e:
        logger.error(f"分析图片时发生错误: {str(e)}")
        return f"分析图片时发生错误: {str(e)}"

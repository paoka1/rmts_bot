"""
高德开放平台天气查询 SDK
ref: https://github.com/Simoon-F/amap-weather
"""

import httpx

from dataclasses import dataclass, field
from typing import List, Optional
from typing import Literal, Optional

from nonebot.log import logger

@dataclass
class LivesItem:
    """实时天气数据项"""
    province: str = ""
    city: str = ""
    adcode: str = ""
    weather: str = ""
    temperature: str = ""
    winddirection: str = ""
    windpower: str = ""
    humidity: str = ""
    reporttime: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "LivesItem":
        """从字典创建LivesItem对象"""
        return cls(
            province=data.get("province", ""),
            city=data.get("city", ""),
            adcode=data.get("adcode", ""),
            weather=data.get("weather", ""),
            temperature=data.get("temperature", ""),
            winddirection=data.get("winddirection", ""),
            windpower=data.get("windpower", ""),
            humidity=data.get("humidity", ""),
            reporttime=data.get("reporttime", "")
        )


@dataclass
class Casts:
    """天气预报数据项（单日）"""
    date: str = ""
    week: str = ""
    dayweather: str = ""
    nightweather: str = ""
    daytemp: str = ""
    nighttemp: str = ""
    daywind: str = ""
    nightwind: str = ""
    daypower: str = ""
    nightpower: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "Casts":
        """从字典创建Casts对象"""
        return cls(
            date=data.get("date", ""),
            week=data.get("week", ""),
            dayweather=data.get("dayweather", ""),
            nightweather=data.get("nightweather", ""),
            daytemp=data.get("daytemp", ""),
            nighttemp=data.get("nighttemp", ""),
            daywind=data.get("daywind", ""),
            nightwind=data.get("nightwind", ""),
            daypower=data.get("daypower", ""),
            nightpower=data.get("nightpower", "")
        )


@dataclass
class Forecasts:
    """天气预报数据"""
    city: str = ""
    adcode: str = ""
    province: str = ""
    reporttime: str = ""
    casts: List[Casts] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Forecasts":
        """从字典创建Forecasts对象"""
        casts_data = data.get("casts", [])
        casts = [Casts.from_dict(cast) for cast in casts_data]
        
        return cls(
            city=data.get("city", ""),
            adcode=data.get("adcode", ""),
            province=data.get("province", ""),
            reporttime=data.get("reporttime", ""),
            casts=casts
        )


@dataclass
class WeatherResponse:
    """天气API响应数据"""
    status: str = ""
    count: str = ""
    info: str = ""
    infocode: str = ""
    lives: List[LivesItem] = field(default_factory=list)
    forecasts: List[Forecasts] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict) -> "WeatherResponse":
        """从字典创建WeatherResponse对象"""
        lives_data = data.get("lives", [])
        lives = [LivesItem.from_dict(live) for live in lives_data]
        
        forecasts_data = data.get("forecasts", [])
        forecasts = [Forecasts.from_dict(forecast) for forecast in forecasts_data]
        
        return cls(
            status=data.get("status", ""),
            count=data.get("count", ""),
            info=data.get("info", ""),
            infocode=data.get("infocode", ""),
            lives=lives,
            forecasts=forecasts
        )
    
    def to_readable_text(self) -> str:
        """
        将天气数据转换为易读的文本描述
        
        Returns:
            人类友好的天气描述文本
        """
        if self.lives:
            # 实时天气
            return self._format_live_weather()
        elif self.forecasts:
            # 天气预报
            return self._format_forecast_weather()
        else:
            return "暂无天气数据"
    
    def _format_live_weather(self) -> str:
        """格式化实时天气"""
        if not self.lives:
            return "暂无实时天气数据"
        
        live = self.lives[0]
        parts = [f"{live.city}当前天气{live.weather}"]
        
        if live.temperature:
            parts.append(f"温度{live.temperature}摄氏度")
        
        if live.winddirection and live.windpower:
            parts.append(f"{live.winddirection}风{live.windpower}级")
        
        if live.humidity:
            parts.append(f"湿度{live.humidity}%")
        
        return "，".join(parts) + "。"
    
    def _format_forecast_weather(self) -> str:
        """格式化天气预报"""
        if not self.forecasts or not self.forecasts[0].casts:
            return "暂无天气预报数据"
        
        forecast = self.forecasts[0]
        city = forecast.city
        casts = forecast.casts
        
        week_names = {
            "1": "周一", "2": "周二", "3": "周三", 
            "4": "周四", "5": "周五", "6": "周六", "7": "周日"
        }
        
        forecast_items = []
        for i, cast in enumerate(casts):
            day_label = "今天" if i == 0 else "明天" if i == 1 else week_names.get(cast.week, cast.week)
            
            # 白天和夜间天气相同时合并描述
            if cast.dayweather == cast.nightweather:
                weather_desc = cast.dayweather
            else:
                weather_desc = f"白天{cast.dayweather}，夜间{cast.nightweather}"
            
            temp_range = f"{cast.nighttemp}~{cast.daytemp}摄氏度"
            
            # 白天和夜间风力相同时合并描述
            if cast.daywind == cast.nightwind and cast.daypower == cast.nightpower:
                wind_desc = f"{cast.daywind}风{cast.daypower}级"
            else:
                wind_desc = None  # 风力不同时省略，避免信息过载
            
            if wind_desc:
                forecast_items.append(f"{day_label}{weather_desc}，{temp_range}，{wind_desc}")
            else:
                forecast_items.append(f"{day_label}{weather_desc}，{temp_range}")
        
        return f"{city}未来{len(casts)}天天气预报：" + "；".join(forecast_items) + "。"


class WeatherError(Exception):
    """天气查询异常"""
    pass


class Weather:
    """高德天气查询类（异步版本）"""
    
    BASE_URL = "https://restapi.amap.com/v3/weather/weatherInfo"
    
    def __init__(self, api_key: str, timeout: float = 10.0):
        """
        初始化天气查询对象
        
        Args:
            api_key: 高德开放平台的 Web API Key
            timeout: 请求超时时间（秒），默认 10 秒
        """
        if not api_key:
            api_key = ""
            logger.warning("初始化 Weather 类时未提供 API key，天气查询将无法使用")
            
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_live_weather(
        self, 
        city: str
    ) -> WeatherResponse:
        """
        获取实时天气
        
        Args:
            city: 城市名称或高德地址位置 adcode，例如："广州" 或 "440100"
            
        Returns:
            天气数据（WeatherResponse对象）
            
        Raises:
            WeatherError: 查询失败时抛出异常
            
        Example:
            >>> w = Weather("your_api_key")
            >>> result = await w.get_live_weather("中山")
            >>> print(result.lives[0].city)
            中山市
        """
        return await self._get_weather(city, extensions="base")
    
    async def get_forecast_weather(
        self, 
        city: str
    ) -> WeatherResponse:
        """
        获取天气预报（未来3-4天）
        
        Args:
            city: 城市名称或高德地址位置 adcode，例如："广州" 或 "440100"
            
        Returns:
            天气预报数据（WeatherResponse对象）
            
        Raises:
            WeatherError: 查询失败时抛出异常
            
        Example:
            >>> w = Weather("your_api_key")
            >>> result = await w.get_forecast_weather("广州")
            >>> print(result.forecasts[0].city)
            广州市
        """
        return await self._get_weather(city, extensions="all")
    
    async def _get_weather(
        self, 
        city: str, 
        extensions: Literal["base", "all"]
    ) -> WeatherResponse:
        """
        内部方法：查询天气信息
        
        Args:
            city: 城市名或 adcode
            extensions: 查询类型，"base" 为实时天气，"all" 为天气预报
            
        Returns:
            天气数据（WeatherResponse对象）
            
        Raises:
            WeatherError: 查询失败时抛出异常
        """
        # 参数验证        
        if not city:
            raise ValueError("城市参数不能为空")
        
        # 构建请求参数
        params = {
            "key": self.api_key,
            "city": city,
            "output": "json",
            "extensions": extensions
        }
        
        try:
            # 使用异步 HTTP 客户端
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                
                # 解析响应
                data = response.json()
                
                # 检查 API 返回的状态
                if data.get("status") != "1":
                    error_info = data.get("info", "未知错误")
                    error_code = data.get("infocode", "")
                    raise WeatherError(f"API 返回错误: {error_info} (code: {error_code})")
                
                # 解析为类型化对象
                return WeatherResponse.from_dict(data)
                
        except httpx.HTTPError as e:
            raise WeatherError(f"网络请求失败: {str(e)}")
        except ValueError as e:
            raise WeatherError(f"JSON 解析失败: {str(e)}")

if __name__ == "__main__":
    import asyncio
    
    async def main():
        api_key = input("请输入高德开放平台的 Web API Key: ").strip()
        weather = Weather(api_key)
        try:
            print("\n=== 查询实时天气 ===")
            live_weather = await weather.get_live_weather("广州")
            print(live_weather.to_readable_text())
            
            print("\n=== 查询天气预报 ===")
            forecast_weather = await weather.get_forecast_weather("广州")
            print(forecast_weather.to_readable_text())
        except WeatherError as e:
            print(f"查询天气失败: {str(e)}")
    
    asyncio.run(main())

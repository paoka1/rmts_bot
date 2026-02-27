"""
图片识别模块
使用豆包 API 对图片进行分析和描述
"""

import httpx

from typing import Optional, Dict, Any


class ImageVision:
    """
    图片识别类，用于通过豆包 API 分析图片内容
    
    使用方法：
        vision = ImageVision(
            api_key="your-api-key",
            model="doubao-seed-1-8-251228",
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        description = await vision.analyze_image(
            image_url="https://example.com/image.jpg",
            focus_point="这张图片中有什么动物？"
        )
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "doubao-seed-1-8-251228",
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> None:
        """
        初始化图片识别客户端
        
        参数：
            api_key: 豆包 API 密钥
            model: 使用的视觉模型名称，默认 doubao-seed-1-8-251228
            base_url: API 的基础 URL
            temperature: 温度参数，控制输出的随机性和创造性 (0.0-2.0)
            max_tokens: 模型输出的最大 token 数量
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client: Optional[httpx.AsyncClient] = None

    def _init_client(self) -> None:
        """初始化 HTTP 客户端（延迟初始化）"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=60.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

    def _build_system_prompt(self, focus_point: Optional[str] = None) -> str:
        """
        构建系统提示词
        
        参数：
            focus_point: 调用者关注的重点内容
            
        返回：
            完整的系统提示词
        """
        base_prompt = """你是一位专业的图像分析助手，擅长准确、详细地描述图片内容。

你的任务是分析用户提供的图片，并提供清晰、有条理的描述。

## 描述要求：

1. **准确性**：确保描述的内容与图片真实呈现的内容一致，不要臆测或添加图片中不存在的内容。

2. **结构化**：按照以下顺序组织描述：
   - 整体场景或主题
   - 主要对象或人物
   - 细节特征（颜色、形状、位置关系等）
   - 背景环境
   - 特殊元素或值得注意的细节

3. **客观性**：使用客观、中立的语言进行描述，避免主观评价，除非被明确要求。

4. **完整性**：尽可能涵盖图片中的所有重要信息，但避免冗余的描述。

5. **可读性**：使用自然流畅的语言，让描述容易理解。"""

        if focus_point:
            base_prompt += f"\n\n## 特别关注：\n\n{focus_point}\n\n在描述图片时，请特别关注上述内容，并在回答中优先提供相关信息。"
        
        return base_prompt

    async def analyze_image(
        self,
        image_url: str,
        focus_point: Optional[str] = None,
        detail: str = "auto"
    ) -> str:
        """
        分析图片并返回描述
        
        参数：
            image_url: 图片的 URL 地址
            focus_point: 可选，调用者关注的重点内容。例如：
                - "请重点描述图片中的人物表情和动作"
                - "请识别图片中的文字内容"
                - "请分析图片中的物品类型和数量"
                - "请描述图片的整体氛围和情感色彩"
            detail: 图片分析的详细程度，可选值：
                - "low": 低分辨率模式，更快但细节较少
                - "high": 高分辨率模式，更详细但消耗更多 token
                - "auto": 自动选择（默认）
                
        返回：
            图片的文字描述
            
        异常：
            可能抛出 HTTP 相关的异常
        """
        # 初始化客户端
        self._init_client()
        
        if self.client is None:
            raise RuntimeError("Failed to initialize HTTP client")
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(focus_point)
        
        # 构建用户提示文本
        user_text = "请详细描述这张图片的内容。" if not focus_point else f"请描述这张图片的内容，特别关注：{focus_point}"
        
        # 构建请求体（豆包 API 格式）
        request_body = {
            "model": self.model,
            "stream": False,
            "tools": [
                {"type": "web_search"}
            ],
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_prompt
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
        }
        
        # 添加可选参数
        if self.temperature is not None:
            request_body["temperature"] = self.temperature
        if self.max_tokens is not None:
            request_body["max_tokens"] = self.max_tokens
        
        # 发送 HTTP POST 请求
        response = await self.client.post(
            f"{self.base_url}/responses",
            json=request_body
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        # 提取描述结果
        if "data" in result and len(result["data"]) > 0:
            first_data = result["data"][0]
            if "content" in first_data and len(first_data["content"]) > 0:
                for content_item in first_data["content"]:
                    if content_item.get("type") == "text":
                        description = content_item.get("text", "")
                        if description:
                            return description.strip()
        
        raise ValueError("API returned empty or invalid response")

    async def analyze_image_with_usage(
        self,
        image_url: str,
        focus_point: Optional[str] = None,
        detail: str = "auto"
    ) -> Dict[str, Any]:
        """
        分析图片并返回描述和 token 使用情况
        
        参数：
            image_url: 图片的 URL 地址
            focus_point: 可选，调用者关注的重点内容
            detail: 图片分析的详细程度（"low", "high", "auto"）
                
        返回：
            包含 description（描述文本）和 usage（使用情况）的字典
            usage 包含：prompt_tokens, completion_tokens, total_tokens
        """
        # 初始化客户端
        self._init_client()
        
        if self.client is None:
            raise RuntimeError("Failed to initialize HTTP client")
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(focus_point)
        
        # 构建用户提示文本
        user_text = "请详细描述这张图片的内容。" if not focus_point else f"请描述这张图片的内容，特别关注：{focus_point}"
        
        # 构建请求体（豆包 API 格式）
        request_body = {
            "model": self.model,
            "stream": False,
            "tools": [
                {"type": "web_search"}
            ],
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_prompt
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
        }
        
        # 添加可选参数
        if self.temperature is not None:
            request_body["temperature"] = self.temperature
        if self.max_tokens is not None:
            request_body["max_tokens"] = self.max_tokens
        
        # 发送 HTTP POST 请求
        response = await self.client.post(
            f"{self.base_url}/responses",
            json=request_body
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        # 提取描述结果
        description = ""
        if "data" in result and len(result["data"]) > 0:
            first_data = result["data"][0]
            if "content" in first_data and len(first_data["content"]) > 0:
                for content_item in first_data["content"]:
                    if content_item.get("type") == "text":
                        description = content_item.get("text", "")
                        break
        
        if not description:
            raise ValueError("API returned empty or invalid response")
        
        # 提取 token 使用情况
        usage = {
            "prompt_tokens": result.get("usage", {}).get("input_tokens", 0),
            "completion_tokens": result.get("usage", {}).get("output_tokens", 0),
            "total_tokens": result.get("usage", {}).get("total_tokens", 0)
        }
        
        return {
            "description": description.strip(),
            "usage": usage
        }

    async def close(self) -> None:
        """关闭客户端连接"""
        if self.client is not None:
            await self.client.aclose()
            self.client = None

if __name__ == "__main__":
    import asyncio
    
    async def main():
        api_key = input("请输入密钥: ")

        vision = ImageVision(
            api_key=api_key,
            model="doubao-seed-1-8-251228",
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        
        try:
            while True:
                image_url = input("请输入图片 URL (或输入 'exit' 退出): ")
                if image_url.lower() == "exit":
                    break
                
                focus_point = input("请输入关注点（可选，直接回车跳过）: ")
                
                try:
                    result = await vision.analyze_image_with_usage(
                        image_url=image_url,
                        focus_point=focus_point if focus_point else None,
                        detail="auto"
                    )
                    print("\n图片描述:\n", result["description"])
                    print("\nToken 使用情况:", result["usage"])
                except Exception as e:
                    print(f"分析图片失败: {e}")
        finally:
            await vision.close()
    
    asyncio.run(main())

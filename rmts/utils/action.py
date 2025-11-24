import httpx

async def send_group_msg(group_id: str, message: str, api_url: str, api_port: str, access_token: str):
    """
    通过 API 发送群聊消息

    参数：
    - group_id: int, 目标群号
    - message: str, 消息内容
    - api_url: str, 基础 API URL
    - access_token: str, 可选，API访问令牌

    返回：
    - dict: API 响应 JSON
    """
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    payload = {
        "group_id": group_id,
        "message": message
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{api_url}:{api_port}/send_group_msg", 
                json=payload, 
                headers=headers
            )
            return response.json()
    except (httpx.RequestError, httpx.TimeoutException) as e:
        return {"status": "error", "error": str(e)}

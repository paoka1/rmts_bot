import asyncio
import httpx
import random
import json

from nonebot.log import logger

from typing import Optional


class LiveRoom:
    """
    直播间信息，字段：
        url: 直播间链接
        title: 直播间标题
        cover: 直播间封面
        status: 直播状态，0：未开播，1：已开播，2：轮播中
    """

    url: str
    title: str
    cover: str
    status: int

    def __init__(self, data: dict) -> None:
        self.status = data['live_status']
        self.url = f"https://live.bilibili.com/{data['room_id']}"
        self.title = data['title']
        self.cover = data['cover_from_user']

    def __str__(self) -> str:
        return f"LiveRoom(title={self.title}, url={self.url}, status={self.status})"


class User:
    """
    用户信息，字段：
        uid: 用户 UID
        code: API 返回码
        name: 用户昵称
        face: 用户头像链接
        message: API 返回消息
        room: 直播间信息
    """

    uid: int
    code: int
    name: str
    face: str
    message: str
    room: LiveRoom

    def __init__(self, data: dict, code: int, message: str) -> None:
        self.code = code
        self.uid = data["uid"]
        self.name = data['uname']
        self.face = data['face']
        self.message = message
        self.room = LiveRoom(data)

    def is_live(self) -> bool:
        return self.room.status == 1

    def __str__(self) -> str:
        return f"User(uid={self.uid}, name={self.name}, face={self.face}, room={self.room})"


def get_header(uid: int) -> dict:
    user_agent_list = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95',
        'Safari/537.36 OPR/26.0.1656.60',
        'Opera/8.0 (Windows NT 5.1; U; en)',
        'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
        'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 '
        '(maverick) Firefox/3.6.10',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/39.0.2171.71 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 '
        '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
    ]
    user_agent = random.choice(user_agent_list) # 随机选择一个 User-Agent

    header = {'User-Agent': user_agent,
              'Accept': 'application/json, text/plain, */*',
              'Origin': 'https://space.bilibili.com',
              'Referer': f'https://space.bilibili.com/{uid}?spm_id_from=333.337.0.0'}

    return header


# get_live_status 用于获取直播状态
async def get_live_status(uid: int) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        url = f"https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids?uids[]={uid}"
        try:
            r = await client.get(url, headers=get_header(uid))
            r.encoding = 'utf-8'
        except Exception as e:
            logger.error(f"请求 {url} 时出错，{e}")
            return None

        try:
            bli_live_data = json.loads(r.text)
        except Exception as e:
            logger.error(f"解析 json 数据时出错，{e}")
            return None

        return bli_live_data


# bili_live_api 接口
async def bli_live_status(uid: int) -> Optional[User]:
    resp = await get_live_status(uid)
    if resp is None:
        return None

    try:
        bli_live_info = User(resp['data'][str(uid)], resp['code'], resp['message'])
    except Exception as e:
        logger.error(f"解析时出错，错误代码：{resp['code']}，错误消息：{resp['message']}，异常信息：{e}")
        return None

    return bli_live_info


if __name__ == '__main__':
    res = asyncio.run(bli_live_status(349921961))
    print(res)

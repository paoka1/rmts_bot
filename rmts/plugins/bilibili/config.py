from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(extra='ignore')

    # 请求直播状态间隔时间，单位秒
    live_request_interval: int
    # 直播订阅群聊和阿婆主
    live_subscriptions: Dict[str, List[str]]

    def get_live_uid_list(self) -> List[str]:
        """
        获取所有订阅的直播用户 UID 列表，返回值：
            所有订阅的直播用户 UID 列表
        """
        uid_list = []
        for uid_subs in self.live_subscriptions.values():
            uid_list.extend(uid_subs)
        return uid_list
    
    def get_live_group_list(self, uid: str) -> List[str]:
        """
        获取订阅了指定直播用户 UID 的群聊列表，参数：
            uid: 直播用户 UID
        返回值：
            订阅了指定直播用户 UID 的群聊列表
        """
        group_list = []
        for group_id, uid_subs in self.live_subscriptions.items():
            if uid in uid_subs:
                group_list.append(group_id)
        return group_list

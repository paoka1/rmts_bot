from typing import Dict
from typing import List

class Status:
    """
    直播状态管理
    """

    def __init__(self, live_subscriptions: Dict[str, List[str]]):
        self.live_status: Dict[str, bool] = {}
    
    def get_live_status(self, uid: str) -> bool:
        """
        获取指定用户的直播状态，参数：
            uid: 用户UID
        返回值：
            bool: 直播状态，True表示直播中，False表示未直播
        """
        return self.live_status.get(uid, False)
    
    def set_live_status(self, uid: str, status: bool):
        """
        设置指定用户的直播状态，参数：
            uid: 用户UID
            status: 直播状态，True表示直播中，False表示未直播
        """
        self.live_status[uid] = status

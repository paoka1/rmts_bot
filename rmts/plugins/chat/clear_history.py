import time

from .pool import RMTSPool

from rmts.utils.config import split_groups

class Vote:
    """
    投票记录
    """
    
    def __init__(self, group_id, sender_id, time):
        """"
        参数：
            group_id: 群号
            sender_id: 发送者QQ号
            time: 投票时间戳
        """
        self.group_id = group_id
        self.sender_id = sender_id
        self.time = int(time)

class ClearHistory:
    """
    基于投票的清理记忆功能
    """

    def __init__(self, rmts: RMTSPool, avliable_groups, threshold: int = 3, timeout:int = 60):
        self.rmts = rmts
        self.avliable_groups = split_groups(avliable_groups)
        self.votes = {}            # 每个群的投票记录
        self.threshold = threshold # 需要的投票数
        self.timeout = timeout     # 投票超时时间，单位秒

    def try_clear(self, group_id: int, sender_id: int) -> str:
        """
        参数：
            group_id: 群号
            sender_id: 发送者QQ号
        """

        if str(group_id) not in self.avliable_groups:
            return "清理记忆功能未启用"
        
        # 首次投票
        if group_id not in self.votes:
            self.votes[group_id] = []
            self.votes[group_id].append(Vote(group_id, sender_id, time.time()))
            return f"1/{self.threshold}"
        
        # 检查上次投票时间是否超时
        last_vote: Vote = self.votes[group_id][-1]
        if last_vote.time + self.timeout < time.time():
            self.votes[group_id] = []
            self.votes[group_id].append(Vote(group_id, sender_id, time.time()))
            return f"1/{self.threshold}"
        
        # 同一个人不能重复投票
        last_votes = self.votes[group_id]
        if sender_id in [vote.sender_id for vote in last_votes]:
            return f"{len(last_votes)}/{self.threshold}"
        
        # 继续投票
        if len(last_votes) + 1 < self.threshold:
            last_votes.append(Vote(group_id, sender_id, time.time()))
            return f"{len(last_votes)}/{self.threshold}"
        
        self.rmts.clear_history(group_id)
        del self.votes[group_id]

        return "指令已执行"
    
import time

from .deepseek import RMTSPlugin

from rmts.utils.config import split_groups

class Vote:
    
    def __init__(self, group_id, sender_id, time):
        self.group_id = group_id
        self.sender_id = sender_id
        self.time = int(time)

class ClearHistory:

    def __init__(self, rmts: RMTSPlugin, avliable_groups, threshold: int = 3, timeout:int = 60):
        self.rmts = rmts
        self.votes = {}
        self.avliable_groups = split_groups(avliable_groups)
        self.threshold = threshold
        self.timeout = timeout

    def try_clear(self, group_id: int, sender_id: int) -> str:
        if str(group_id) not in self.avliable_groups:
            return "清理记忆功能未启用"
        
        if group_id not in self.votes:
            self.votes[group_id] = []
            self.votes[group_id].append(Vote(group_id, sender_id, time.time()))
            return f"1/{self.threshold}"
        
        last_vote: Vote = self.votes[group_id][-1]
        if last_vote.time + self.timeout < time.time():
            self.votes[group_id] = []
            self.votes[group_id].append(Vote(group_id, sender_id, time.time()))
            return f"1/{self.threshold}"
        
        last_votes = self.votes[group_id]
        if sender_id in [vote.sender_id for vote in last_votes]:
            return f"{len(last_votes)}/{self.threshold}"
        
        if len(last_votes) + 1 < self.threshold:
            last_votes.append(Vote(group_id, sender_id, time.time()))
            return f"{len(last_votes)}/{self.threshold}"
        
        self.rmts.clear_history()
        return "boom!"
    
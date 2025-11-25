class WeiShu:

    def __init__(self):
        self.wait_list = {}

    def add_wait(self, group_id: int, user_id: int) -> str:
        if group_id not in self.wait_list:
            self.wait_list[group_id] = []
        if user_id not in self.wait_list[group_id]:
            self.wait_list[group_id].append(user_id)
            return "已预约卫戍"
        else:
            return "你已经预约过了"

    def remove_all(self, group_id: int):
        self.wait_list[group_id] = []

    def get_all(self, group_id: int):
        return self.wait_list.get(group_id, [])

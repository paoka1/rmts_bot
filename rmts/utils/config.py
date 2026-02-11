# 配置与加载

def split_groups(groups_str: str) -> list[str]:
    """
    分割群列表，推荐使用 split_groups_int 获取整数列表，便于后续比较
    """
    groups = str(groups_str).split(",")
    if groups == [""]:
        return []
    return groups

def split_groups_int(groups_str: str) -> list[int]:
    """
    分割群列表并转换为整数
    """
    groups = split_groups(groups_str)
    return [int(group) for group in groups if group.isdigit()]

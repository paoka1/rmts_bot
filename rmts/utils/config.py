def split_groups(groups_str) -> list[str]:
    """
    分割群列表
    """
    groups = str(groups_str).split(",")
    if groups == [""]:
        return []
    return groups

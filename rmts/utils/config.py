def split_groups(groups_str: str) -> list[str]:
    groups = groups_str.split(",")
    if groups == [""]:
        return []
    return groups

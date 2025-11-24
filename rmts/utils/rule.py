from nonebot.adapters.onebot.v11 import Event, PokeNotifyEvent

# 自定义 Rule：判断是否是戳到bot的poke事件
async def is_poke_me(event: Event) -> bool:
    return isinstance(event, PokeNotifyEvent) and event.is_tome()

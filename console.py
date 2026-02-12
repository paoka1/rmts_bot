import nonebot

from nonebot.adapters.console import Adapter as CONSOLEAdapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(CONSOLEAdapter)

# nonebot.load_builtin_plugins('echo')
nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()

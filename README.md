# rmts bot

以迷迭香（Rosmontis）为核心设定的 QQ 群聊机器人，基于 NoneBot2 框架和 OneBotv11 协议开发，支持 AI 对话、B站直播推送、互动游戏等多种功能

## 功能介绍

### AI 对话

- 支持 Function Calling，可调用自定义函数，已支持的函数功能调用：
  - 发送戳一戳
  - 发送表情
  - 获取当前时间
  - 通过日期获取过生日的干员，通过名字获取干员的生日
  - 天气查询
  - 全局、个人记忆增查
  - 干员档案查询
  
- 群组独立的对话历史管理
- 艾特机器人或戳一戳触发对话
- 基于投票机制的重置功能（艾特发送`清除记忆`）

### B站直播推送
- 订阅指定 UP 主的直播状态
- 开播自动推送封面、标题和直播间链接
- 支持多群订阅和多 UP 主监控

### 轮盘游戏
- 俄罗斯轮盘小游戏（艾特发送`香香轮盘`、`香香开枪`）
- 惩罚机制为禁言
- 可配置哑火概率

### Minecraft服务器状态查询

- 查询服务器状态（艾特发送`查询状态`）
- 玩家上线、离线提醒

等...

## 部署配置

### 环境要求
- Python >= 3.9, < 4.0
- OneBot V11 协议端（如 [NapCat](https://napneko.github.io/) 等）

### 部署步骤

1.克隆项目

```bash
git clone https://github.com/paoka1/rmts_bot
cd rmts_bot
```

2.安装依赖

该命令只安装运行时依赖，开发环境依赖安装命令见下文

```bash
pip install -e .
```

3.配置环境变量

详见`.env`文件，根据实际情况修改配置，主要配置项：

**AI 对话相关**

```bash
BASE_URL=https://api.deepseek.com   # OpenAI API 兼容端点
MODEL_NAME=deepseek-chat            # 模型名称
API_KEY=sk-xxx                      # API 密钥
MAX_HISTORY_LENGTH=80               # 最大历史消息长度
```

**功能开关与群组配置**

```bash
# 问候功能可用群组，多个用逗号分隔
GREET_AVAILABLE_GROUPS=123456,789012
# 清除历史功能可用群组
CLEAR_HISTORY_AVAILABLE_GROUPS=123456,789012
# 轮盘游戏可用群组
ROULETTE_AVAILABLE_GROUPS=123456,789012
# B站直播订阅配置，JSON 格式：{"群号": ["UP主UID"]}
LIVE_SUBSCRIPTIONS={"123456": ["123456789","987654321"]}
```

**OneBot 连接配置**

在 `.env` 中配置 OneBot 连接信息：
```bash
HOST=127.0.0.1 # 按实际填写
PORT=8080      # 按实际填写
ONEBOT_ACCESS_TOKEN= # 与协议端保持一致
```

等...

4.运行机器人

进入 Bot 项目目录，运行：

```bash
nb run
```

## 开发指南

### 项目结构
```
rmts/
├── plugins/         # 插件目录
│   ├── bilibili/    # B站直播推送
│   ├── chat/        # AI 对话
│   ├── greet/       # 问候功能
│   ├── minecraft/   # Minecraft服务器状态
│   ├── roulette/    # 轮盘游戏
│   └── weishu/      # 卫戍协议
├── resources/       # 资源文件
│   ├── json/        # 数据
│   └── images/      # 图片资源
└── utils/           # 通用工具
    ├── action.py    # 消息发送等操作
    ├── config.py    # 配置工具
    ├── info.py      # 信息获取
    └── rule.py      # 自定义规则
```

### 添加新插件

1.在 `rmts/plugins/` 下创建新目录

```bash
mkdir rmts/plugins/your_plugin
```

2.创建 `__init__.py` 并编写插件逻辑

```python
from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent

# 创建消息监听器，监听所有消息
hello_matcher = on_message()

@hello_matcher.handle()
async def handle_hello(event: MessageEvent):
    """
    收到消息后判断内容是否包含 'hello'，如果是就回复 'world'
    """
    text = event.get_plaintext().lower()
    if "hello" in text:
        await hello_matcher.finish("world")
```

3.NoneBot2 会自动加载 `rmts/plugins/` 下的所有插件

### 为 chat 插件添加 Function Calling

Function Calling 允许 AI 调用预定义的函数来执行特定操作

1.在 `rmts/plugins/chat/functions/action/`、`info/` 等目录下编写辅助模块，编写的模块在 `__init__.py` 中调用，如果实现的功能较为简单，可以直接在 `__init__.py` 编写逻辑

其中 Bot 和外界的动作交互应在 `action` 中编写，获取信息应在 `info` 中编写，以此类推，如果需要实现不同于两者的功能，可以创建独立的文件夹，如 `rmts/plugins/chat/functions/xxx/`

2.在选择的目录下注册函数

```python
from rmts.plugins.chat.function_calling import FunctionDescription, function_container

# 创建函数描述
func_desc = FunctionDescription(name="function_name", description="函数功能描述")

# 添加参数（AI 提供）
func_desc.add_param(name="param1", description="参数描述", param_type="string", required=True)
func_desc.add_enum_param(name="param2", description="选择参数", enum_values=["选项1", "选项2"], required=True)
func_desc.add_list_param(name="param3", description="列表参数", item_type="integer", required=False)
func_desc.add_dict_param(name="param4", description="字典参数", value_type="string", required=False)

# 添加注入参数（系统自动提供，AI 无需传递）
func_desc.add_injection_param(name="group_id", description="群组的唯一标识符")

# 使用装饰器注册函数
@function_container.function_calling(func_desc)
async def function_name(param1: str, param2: str, param3: list, param4: dict, group_id: int) -> str:
    # 函数实现
    return "执行结果"
```

**可用的参数添加方法：**
- `add_param`: 基本类型参数（`string`、`number`、`integer`、`boolean`）
- `add_enum_param`: 枚举参数（从预定义选项中选择）
- `add_list_param`: 列表参数（可指定元素类型）
- `add_dict_param`: 字典参数（可指定值类型）
- `add_injection_param`: 注入参数（系统自动提供，如 `group_id`、`user_id`等...）

Function Calling 函数应拥有一个 `str` 类型的返回值，对参数的数量没有要求

3.系统会自动扫描并注册，AI 即可调用该函数

### 修改现有插件

1. 找到对应插件目录，如 `rmts/plugins/bilibili/`
2. 修改相关代码文件
3. 如需新增配置项，在插件的 `config.py` 中添加字段
4. 在 `.env` 文件中添加对应的环境变量

### 开发工具

项目配置了代码检查工具：
```bash
# 安装开发依赖
pip install -e ".[dev]"

# 使用 ruff 格式化代码
ruff format .

# 使用 pyright 检查类型
pyright
```

### 测试工具

如果你没有配置 NapCat 等协议端，可以使用 [matcha](https://github.com/A-kirami/matcha) 模拟 QQ 进行测试（推荐），或者使用 [Console 适配器](https://github.com/nonebot/adapter-console)

### 提交 Pull Request

1.Fork 本仓库

2.创建特性分支

```bash
git checkout -b feature/your-feature
```

3.提交更改

```bash
git add .
git commit -m "描述你的更改"
```

4.推送到你的仓库

```bash
git push origin feature/your-feature
```

5.在 GitHub 上创建 Pull Request，描述你的更改内容

## 致谢

- [Nonebot2](https://github.com/nonebot/nonebot2)：跨平台 Python 异步聊天机器人框架
- [NapCat](https://github.com/NapNeko/NapCatQQ)：现代化的基于 NTQQ 的 Bot 协议端实现
- [matcha](https://github.com/A-kirami/matcha)：模拟聊天交互的辅助开发工具
- [ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData)：《明日方舟》游戏数据
- [PRTS wiki](https://prts.wiki/w/%E9%A6%96%E9%A1%B5)：由游戏明日方舟爱好者搭建并协作编写的非营利wiki类资料站点
- [Console 适配器](https://github.com/nonebot/adapter-console)：NoneBot2 终端适配器
- deepseek、高德等服务提供平台

## 参考文档

- [NoneBot2 文档](https://nonebot.dev/)
- [OneBot V11 标准](https://github.com/botuniverse/onebot-11)
- [NapCat 文档](https://napneko.github.io/)

## 许可证

本项目采用 LICENSE 文件中指定的许可证

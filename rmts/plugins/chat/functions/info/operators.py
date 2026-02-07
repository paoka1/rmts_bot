"""
干员信息
ref: https://github.com/Kengxxiao/ArknightsGameData
"""

import os
import json
import aiofiles

from pathlib import Path
from openai import AsyncOpenAI
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union


@dataclass
class StoryInfo:
    """故事信息"""
    title: str  # 故事标题，如"基础档案"、"临床诊断分析"
    content: List[str]  # 故事内容，按行分割
    
    def get_full_text(self) -> str:
        """获取完整文本"""
        return "\n".join(self.content)


@dataclass
class OperatorInfo:
    """干员信息"""
    char_id: str  # 角色ID
    info_name: str  # 信息名称
    is_limited: bool  # 是否限定
    is_alternative: bool = False  # 是否异格
    stories: List[StoryInfo] = field(default_factory=list)  # 档案故事列表
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OperatorInfo":
        """从字典创建干员信息对象"""
        char_id = data.get("charID", "")
        info_name = data.get("infoName", "Unknown")
        is_limited = data.get("isLimited", False)
        
        stories = []
        story_text_audio = data.get("storyTextAudio", [])
        
        # 从基础档案中提取真实的干员代号
        name = None
        for audio_item in story_text_audio:
            story_title = audio_item.get("storyTitle", "")
            story_list = audio_item.get("stories", [])
            
            # 提取有意义的 storyText
            for story in story_list:
                story_text = story.get("storyText", "")
                if story_text and story_text.strip():
                    # 按回车分割文本
                    content_lines: List[str] = [line.strip() for line in story_text.split("\n") if line.strip()]
                    
                    # 如果是基础档案且还没有找到真实名字，尝试提取【代号】
                    if story_title == "基础档案" and name is None:
                        name = content_lines[0].split("】")[-1].strip()
                        name = name.replace("“", "").replace("”", "")  # 去除引号
                    
                    story_info = StoryInfo(
                        title=story_title,
                        content=content_lines
                    )
                    stories.append(story_info)
        
        # 如果找到了真实名字，使用它；否则使用原来的 infoName
        if name:
            info_name = name
        
        return cls(
            char_id=char_id,
            info_name=info_name,
            is_limited=is_limited,
            stories=stories
        )
    
    def get_story_by_title(self, title: str) -> Optional[StoryInfo]:
        """根据标题获取故事"""
        for story in self.stories:
            if story.title == title:
                return story
        return None
    
    def get_all_story_titles(self) -> List[str]:
        """获取所有故事标题"""
        return [story.title for story in self.stories]
    
    def to_string(self) -> str:
        """转换为可读字符串"""
        lines = [
            f"干员ID: {self.char_id}",
            f"名称: {self.info_name}",
            f"是否限定: {'是' if self.is_limited else '否'}",
            "\n档案信息:"
        ]
        
        for story in self.stories:
            lines.append(f"\n【{story.title}】")
            lines.extend(story.content)
        
        return "\n".join(lines)


class OperatorInfoBuilder:
    """
    干员信息构建类
    """

    def __init__(self,
                 *,
                 api_key: Optional[str] = None,
                 resource_path: str = "rmts/resources/json/operators/handbook_info_table.json",
                 output_path: str = "rmts/resources/json/operators/operators_info.json",
                 base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-chat",
                 prompt: Optional[str] = None,
                 temperature: float = 0.5,
    ):
        """
        构建干员信息字符串
        参数：
            resource_path: 资源文件路径
            api_key: API密钥
            output_path: 输出文件路径
            base_url: API基础URL
            model: 使用的模型
            prompt: 可选的提示语，为空时使用默认提示语
            temperature: 生成文本的随机程度，值越高生成的文本越随机，值越低生成的文本越确定
        """

        if prompt is None:
            self.prompt = self.get_system_prompt()
        else:
            self.prompt = prompt
        
        self.api_key = api_key
        self.resource_path = Path(os.getcwd()) / resource_path
        self.output_path = Path(os.getcwd()) / output_path
        self.base_url = base_url
        self.model = model
        self.temperature = temperature

        self.operators_data: Dict[str, OperatorInfo] = {} # 干员名称到干员信息的映射
        self.client: Optional[AsyncOpenAI] = None  # OpenAI 客户端

    def get_system_prompt(self) -> str:
        """
        获取系统提示语
        """

        prompt = """你是一位专业的档案整理专家，擅长将详细的第一人称档案资料转换为精炼、客观的第三人称描述。

你的任务是将明日方舟干员的档案信息进行整理和改写，输出一份供其他AI使用的干员信息摘要。

## 改写要求：

1. **人称转换**：
   - 将所有第一人称（"我"、"你"）改为第三人称叙述
   - 用"博士"代替原文中的"你"
   - 保持客观、中立的叙述口吻

2. **信息整合**：
   - 保留所有关键信息（基础档案、身份背景、能力特点、经历故事、人际关系等）
   - 将分散在各个档案中的信息整合为流畅的段落
   - 删除重复或冗余的描述，但不能过度简化

3. **内容结构**：
   - 第一段：基础信息（代号、性别、种族、出身地、生日、身高等）
   - 第二段：感染情况与身体状况（矿石病感染、体检结果、特殊体质等）
   - 第三段：背景履历（出身、经历、如何加入罗德岛）
   - 第四段及以后：能力特点、性格特征、人际关系、重要事件等
   - 最后：总结性描述或他人评价

4. **文风要求**：
   - 保持叙事的连贯性和可读性
   - 适当保留一些细节和情感色彩，使人物形象立体
   - 长度控制在原文的50%到60%左右
   - 避免过于生硬的条目式罗列

5. **特殊处理**：
   - 对话引用可以保留，但需要标明说话者
   - 重要的数据（如融合率、结晶密度）需要保留
   - 能力评价（物理强度、战场机动等）需要整合到描述中
   - 若出现多份档案，则说明干员有多种身份或经历，并整合所有档案的信息进行描述

## 输出格式：

以干员代号开头，然后是多个自然段落的叙述性文本，不需要使用【】标记或明显的分段标题。

## 示例风格：

澄闪，原名苏茜·格里特，女性菲林，1月7日出生于维多利亚北部边境城市博森德尔，身高159cm。作为格里特夫妇的第六个孩子，她在贫困的家庭中长大，兄妹众多。

她是一名矿石病感染者，体细胞与源石融合率为4%，血液源石结晶密度为0.27u/L。她的源石技艺适应性极高，但由于家庭经济原因，未能在当地术师学院完成学业。感染矿石病后，她的源石技艺开始失控，表现为不间断且无意识的静电释放。格拉尼曾抱怨说："最近澄闪小姐的静电越来越强了，为她做诊疗的干员一定要做静电保护！"

（继续详细但精炼的叙述...）

现在，请对下面的干员档案进行整理改写："""

        return prompt
    
    def load_operators(self):
        """
        从 JSON 文件加载所有干员信息
        """
        with open(self.resource_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        handbook_dict = data.get("handbookDict", {})
        
        for idx_name, char_data in handbook_dict.items():
            if idx_name.startswith("npc_"):
                continue  # 跳过 NPC 数据

            operator_info = OperatorInfo.from_dict(char_data)
            name = operator_info.info_name
            if name in self.operators_data: # 异格干员
                name = name + "[异格]"
                operator_info.is_alternative = True
                if name in self.operators_data: # 二次异格
                    name = name.replace("[异格]", "[二次异格]")
            self.operators_data[name] = operator_info

    def _init_client(self) -> None:
        """初始化 OpenAI 客户端"""
        if self.client is None:
            if self.api_key is None:
                raise ValueError("API key is required for summarization")
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

    async def summarize_operator(self, operator: Union[str, List[OperatorInfo]]) -> Dict:
        """
        对单个干员的信息进行总结，并返回使用情况
        参数：
            operator: 干员名称（str）或干员信息对象（OperatorInfo）
        返回：
            包含 summary（总结文本）和 usage（使用情况）的字典
            usage 包含：prompt_tokens, completion_tokens, total_tokens
        注意：
            如果干员已经异格，则会自动整合多份档案进行总结
        """
        # 初始化客户端
        self._init_client()
        
        # 获取干员信息对象
        if isinstance(operator, str):
            operator_info = self.get_operator_info_by_name(operator)
            if operator_info is None:
                raise ValueError(f"未找到干员: {operator}")
        else:
            operator_info = operator
        
        # 构建用户消息（干员的完整档案信息）
        user_message = ""
        for op in operator_info:
            user_message += op.to_string() + "\n\n"

        if self.client is None:
            raise ValueError("OpenAI client is not initialized")
        
        # 调用 API 进行总结
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature,
            stream=False
        )
        
        # 提取总结结果和使用情况
        summary = response.choices[0].message.content
        usage = response.usage
        
        return {
            "summary": summary if summary else "",
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            }
        }

    def get_operator_info_by_name(self, name: str) -> Optional[List[OperatorInfo]]:
        """
        根据干员名称获取干员信息
        参数：
            name: 干员名称
        返回：
            包含 OperatorInfo 对象的列表，如果未找到则返回 None
        """
        # 尝试查找干员及其所有异格版本
        result = [self.operators_data[name + suffix] 
                  for suffix in ["", "[异格]", "[二次异格]"] 
                  if name + suffix in self.operators_data]
        return result if result else None
    
    async def build_all_operators_info(self, max_concurrent: int = 5):
        """
        构建所有干员的信息摘要，并保存到输出文件
        参数：
            max_concurrent: 同时发送请求的上限，默认为5
        """
        # 检查输出文件是否存在
        if self.output_path.exists():
            response = input(f"文件 {self.output_path} 已存在，是否覆盖？(y/n): ").strip().lower()
            if response != 'y':
                print("操作已取消")
                return
        
        # 确保输出目录存在
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化客户端
        self._init_client()
        
        # 准备所有需要处理的干员（过滤掉异格，因为会在原干员处理时一起处理）
        operators_list = [name for name, op_info in self.operators_data.items() if not op_info.is_alternative]
        total_count = len(operators_list)
        
        print(f"开始处理 {total_count} 个干员...")
        
        # 结果字典
        results = {}
        
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # 统计信息
        total_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        
        # 处理单个干员的包装函数
        async def process_operator(name: str):
            async with semaphore:
                try:
                    print(f"正在处理: {name}")
                    result = await self.summarize_operator(name)
                    return name, result, None
                except Exception as e:
                    print(f"处理 {name} 时出错: {e}")
                    return name, None, str(e)
        
        # 分批处理
        batch_size = max_concurrent
        for i in range(0, total_count, batch_size):
            batch = operators_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_count + batch_size - 1) // batch_size
            
            print(f"\n{'='*50}")
            print(f"处理批次 {batch_num}/{total_batches} (干员 {i+1}-{min(i+batch_size, total_count)}/{total_count})")
            print(f"{'='*50}")
            
            # 并发处理当前批次
            tasks = [process_operator(name) for name in batch]
            batch_results = await asyncio.gather(*tasks)
            
            # 更新结果
            for name, result, error in batch_results:
                if result is not None and error is None:
                    results[name] = {
                        "summary": result["summary"]
                    }
                    # 累计使用量
                    total_usage["prompt_tokens"] += result["usage"]["prompt_tokens"]
                    total_usage["completion_tokens"] += result["usage"]["completion_tokens"]
                    total_usage["total_tokens"] += result["usage"]["total_tokens"]
                else:
                    results[name] = {
                        "summary": "",
                        "error": error if error else "未知错误"
                    }
            
            # 保存当前结果
            save_data = {
                "operators": results,
                "statistics": {
                    "total_operators": len(results),
                    "completed": len([r for r in results.values() if "error" not in r]),
                    "failed": len([r for r in results.values() if "error" in r]),
                    "usage": total_usage
                }
            }
            
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ 批次 {batch_num} 完成，已保存到 {self.output_path}")
            print(f"  进度: {len(results)}/{total_count} 个干员")
            print(f"  当前批次使用: {sum(r.get('usage', {}).get('total_tokens', 0) for _, r, _ in batch_results if r)} tokens")
        
        print(f"\n{'='*50}")
        print(f"所有干员处理完成！")
        print(f"{'='*50}")
        print(f"总计: {len(results)} 个干员")
        print(f"成功: {len([r for r in results.values() if 'error' not in r])} 个")
        print(f"失败: {len([r for r in results.values() if 'error' in r])} 个")
        print(f"\n总使用情况:")
        print(f"  输入 tokens: {total_usage['prompt_tokens']}")
        print(f"  输出 tokens: {total_usage['completion_tokens']}")
        print(f"  总计 tokens: {total_usage['total_tokens']}")


class OperatorInfoManager:
    """
    干员信息加载查询
    """

    def __init__(self, json_file_path: str = "rmts/resources/json/operators/operators_info.json") -> None:
        """
        初始化干员信息类
        参数：
            json_file_path: 干员信息 JSON 文件路径
        """

        self.json_file_path = Path(os.getcwd()) / json_file_path
        self.operators_info: Dict[str, Dict] = {}  # 干员名称到信息的映射

    async def load_operators_info(self):
        """
        加载干员信息
        """
        
        async with aiofiles.open(self.json_file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
        
        # 从 JSON 中提取 operators 字段
        self.operators_info = data.get("operators", {})

    async def get_operator_info_by_name(self, name: str) -> Optional[Dict]:
        """
        根据干员名称获取干员信息
        参数：
            name: 干员名称
        返回：
            包含干员信息的字典，如果未找到则返回 None
        """

        if not self.operators_info:
            await self.load_operators_info()

        return self.operators_info.get(name, None)

if __name__ == "__main__":
    import asyncio
    
    async def test_builder():
        """测试 OperatorInfoBuilder：加载原始档案并使用 API 总结"""
        # 示例1：加载并打印干员原始档案
        builder = OperatorInfoBuilder()
        builder.load_operators()
    
        print(f"已加载干员数量: {len(builder.operators_data)}")
        
        operator_name = input("请输入要查询的干员名称（如：澄闪）：").strip()
        operator_info = builder.get_operator_info_by_name(operator_name)
        
        if operator_info:
            print("\n=== 原始档案 ===")
            for op in operator_info:
                print(op.to_string())
                print("\n----------------\n")
            
            # 示例2：使用 API 总结干员信息并获取费用信息
            apikey = input("\n请输入 API Key 以测试总结功能（或直接按回车跳过）：").strip()
            if not apikey:
                print("未提供 API Key，跳过总结测试")
                return
            
            builder_with_api = OperatorInfoBuilder(api_key=apikey, temperature=0.5)
            builder_with_api.load_operators()
            
            result = await builder_with_api.summarize_operator(operator_name)
            
            print("\n=== AI 总结 ===")
            print(result["summary"])
            
            print("\n=== 使用情况 ===")
            usage = result["usage"]
            print(f"输入 tokens: {usage['prompt_tokens']}")
            print(f"输出 tokens: {usage['completion_tokens']}")
            print(f"总计 tokens: {usage['total_tokens']}")
        else:
            print(f"未找到干员: {operator_name}")

    async def test_manager():
        """测试 OperatorInfoManager：加载并查询已生成的干员信息"""
        manager = OperatorInfoManager()
        
        print("正在加载干员信息...")
        await manager.load_operators_info()
        
        print(f"已加载干员数量: {len(manager.operators_info)}")
        
        operator_name = input("请输入要查询的干员名称（如：澄闪）：").strip()
        
        operator = await manager.get_operator_info_by_name(operator_name)
        if operator:
            print("\n=== 干员信息摘要 ===")
            print(operator.get("summary", "无摘要信息"))
        else:
            print(f"未找到干员: {operator_name}")

    async def build_all():
        """构建所有干员的信息摘要"""
        apikey = input("请输入 API Key 以构建所有干员信息（或直接按回车跳过）：").strip()
        if not apikey:
            print("未提供 API Key，跳过构建")
            return
        
        builder = OperatorInfoBuilder(api_key=apikey)
        builder.load_operators()
        await builder.build_all_operators_info(max_concurrent=25)
    
    print("=" * 60)
    print("干员信息系统测试")
    print("=" * 60)
    print("1. 测试 OperatorInfoBuilder（加载原始档案并使用 API 总结）")
    print("2. 测试 OperatorInfoManager（查询已生成的干员摘要信息）")
    print("3. 构建所有干员信息摘要（需要 API Key）")
    print("=" * 60)
    
    choose = input("请选择操作 (输入1/2/3): ").strip()
    if choose == '1':
        asyncio.run(test_builder())
    elif choose == '2':
        asyncio.run(test_manager())
    elif choose == '3':
        asyncio.run(build_all())
    else:
        print("无效选择，程序结束")

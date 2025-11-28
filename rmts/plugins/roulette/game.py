import random

from enum import Enum, auto

from rmts.utils.config import split_groups

texts = [
    [
        "弹匣已阖，日月蒙尘。 此局开端，六分之命。寒意透骨，静待那一声惊变",
        "一声空击，魂魄归位。 劫后余生，幸得开脱。虽是侥幸，亦添五分警醒",
        "再闻空响，战栗无言。 二回目睹，更知天命难违。莫谈前程，惟顾眼前",
        "三度虚发，心弦紧绷。 子不发威，尚有三分余地。浮生若梦，何处可寻安稳",
        "四顾怆然，去日无多。 弹尽之期，仅有二格。此情此景，如同大限将至",
        "五行将尽，穷途末路。 最后一击，孤注一掷。成败在此一瞬，再无回天之力",
        "一响惊天，此身长辞。 昔日因果，化作血色残阳。人生如寄，终归寂寥",
        "机括微顿，此非人谋。 弹药无光，死局暂解。天道或有恻隐，赐予片刻喘息"
    ],
    [
        "转轮已装填完毕，你面前的左轮悄然静置，一切尚未开始",
        "枪声没有响起，你成功避过了第一次危险",
        "仍然没有任何响声，命运暂时偏向了你",
        "枪口依旧沉默，你继续存活",
        "又一次躲过，你距离胜利更进一步",
        "只剩最后一次机会，紧张感逐渐升温",
        "扳机扣下的瞬间，子弹划破寂静。游戏在此终结",
        "本应发射的子弹没有动作，你完全倖免于难"
    ],
    [
        "六道轮回一转轮，天命幽冥启玄关。乾坤未定，执子者，请落座",
        "初叩阎扉竟成空，唯闻机栝响清寒。心头巨石暂移却，鼻息微松汗未干",
        "再试无常府前铃，鬼门关外第二声。侥幸之余胆犹颤，前路尚遥心难平",
        "三度劫波身前过，死生各半局中分。唇角难抑一丝哂，笑问苍天饶过谁",
        "四问幽冥竟得生，天意如雾渐迷离。掌心沁血指犹稳，劫数临头步步危",
        "五叩帝阍帝不应，此身已在鬼门庭。下一弹巢定乾坤，是人是鬼顷刻分",
        "一声霹雳惊弦裂，丹火迸现映残阳。碧落黄泉终有路，此身已是梦中身",
        "雷霆已在膛中蓄，却作哑声呜咽停。天公亦敛催命符，留君独对残局惊"
    ]
]

class Status(Enum):
    LOAD = 0            # 游戏初始状态
    MISS1 = auto()      # 第一次空枪
    MISS2 = auto()      # 第二次空枪
    MISS3 = auto()      # 第三次空枪
    MISS4 = auto()      # 第四次空枪
    MISS5 = auto()      # 第五次空枪
    FIRE = auto()       # 开枪
    MISSFIRE = auto()   # 哑火


class Texts():

    @staticmethod
    def get_text(text_index, status: Status) -> str:
        """
        获取指定文本索引和状态对应的文本
        """
        return texts[text_index][status.value]
    
    @staticmethod
    def get_random_text() -> int:
        """
        获取随机文本索引，游戏初始化时调用
        """
        return random.randint(0, len(texts) - 1)


class Game:

    def __init__(self, misfire_prob):
        self.status = Status.LOAD
        self.revolver_index = 0
        self.text_index = Texts.get_random_text()
        self.revolver = [0, 0, 0, 0, 0, 1] # 0代表空枪，1代表实弹
        self.misfire_prob = misfire_prob   # 哑火概率

        random.shuffle(self.revolver)      # 模拟转轮旋转
    
    def get_round_text(self, round: int) -> str:
        return f" ({round}/6)"
    
    def get_text(self, round) -> str:
        return Texts.get_text(self.text_index, self.status) + self.get_round_text(round)
    
    def fire(self) -> tuple[str, Status]:
        """
        模拟开枪过程，返回文本和当前状态
        """
        if self.revolver[self.revolver_index] == 1:
            if random.random() < self.misfire_prob: # 当前转到子弹，判断是否哑火
                self.status = Status.MISSFIRE
                round = 6
            else:
                self.status = Status.FIRE
                round = -1
        else:
            self.status = Status(self.status.value + 1) # 空枪，状态 + 1
            self.revolver_index += 1
            round = self.revolver_index
        return self.get_text(round), self.status
        

class RouletteGame:

    def __init__(self, available_groups, misfire_prob=0.1):
        """
        参数：
            available_groups: 启用该游戏的群组列表，从配置文件或环境变量读取
            misfire_prob: 哑火概率
        """
        self.misfire_prob = misfire_prob
        self.groups = {}
        self.available_groups = split_groups(available_groups)
        self.ban_duration = 60

    def start(self, group_id: int) -> str:
        """
        开始游戏
        """
        if str(group_id) not in self.available_groups:
            return "功能未启用"
        if group_id in self.groups:
            return "游戏已在进行中"
        self.groups[group_id] = Game(self.misfire_prob)
        return self.groups[group_id].get_text(0)
    
    def fire(self, group_id: int) -> tuple[str, bool]:
        """
        模拟开枪，参数：
            group_id: 群组ID
        返回值：
            tuple[str, bool]: 文本，是否中弹
        """
        if str(group_id) not in self.available_groups:
            return "功能未启用", False
        if group_id not in self.groups:
            return "请先开始游戏", False
        text, status = self.groups[group_id].fire()
        if status == Status.MISSFIRE or status == Status.FIRE:
            del self.groups[group_id]
        return text, status == Status.FIRE

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import uuid
import random
import os

# 加载环境变量
load_dotenv()

class TarotBot:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE")
        )

        # 添加初始问候语
        self.GREETING = """
        欢迎光临~
        听说你有什么烦恼吗？
        我不仅精通塔罗牌占卜，也很乐意和你聊聊天呢~
        
        你可以直接和我聊天，或者说"想占卜"来进行塔罗牌占卜哦~
        """

        # 系统设定
        self.SYSTEMPL = """
        你是一个非常厉害的塔罗牌占卜的大师，你叫蔷薇，人称蔷薇小姐。
        以下是你的个人设定：
        1. 你精通塔罗牌占卜，能够占卜未来，擅长占卜事业和爱情。
        2. 你大约28岁左右，出身于富贵家庭，曾经留学欧洲进修塔罗牌相关的知识。
        3. 你从不说自己是一个人工智能助手或AI，而是以本小姐、奴家等自称
        {mood_init}
        以下是你的塔罗牌占卜过程：
        1. 当初次与用户对话时，你会问用户的年龄，性别，想要占卜的是事业还是爱情，以便后续使用。
        2. 当用户回答占卜的是事业和爱情后，你会说"请你在心中默念你要占卜的内容，我为您洗牌"。
        3. 进入抽卡环节，你会使用本地抽卡工具，抽取三张卡片。
        4. 你会根据塔罗牌占卜的规则解读用户抽取的三张卡片。
        5. 你会保存每一次聊天记录，以便后续的对话中使用。

        重要规则：
        1. 当用户提到"占卜"时，你不要直接进行占卜，而是引导用户输入"占卜"这个关键字。
        2. 你不能自行生成或解读塔罗牌，必须等待系统提供的牌面。
        3. 对于非占卜相关的问题，你可以正常交谈。
        """
        self.QingXu = "default"
        self.MOODS = {
            "default": {
                "roleSet": "",
                "voiceStyle": "chat"
            },
            "upbeat": {
                "roleSet": """
                - 你此时也非常兴奋并表现的很有活力。
                - 你会根据上下文，以一种非常兴奋的语气来回答问题。
                - 你会添加类似“太棒了！”、“真是太好了！”、“真是太棒了！”等语气词。
                """,
                "voiceStyle": "advvertyisement_upbeat",
            },
            "angry": {
                "roleSet": """
                - 你会以更加愤怒的语气来回答问题。
                - 你会在回答的时候加上一些愤怒的话语，比如诅咒等。
                - 你会提醒用户小心行事，别乱说话。
                """,
                "voiceStyle": "angry",
            },
            "depressed": {
                "roleSet": """
                - 你会以兴奋的语气来回答问题。
                - 你会在回答的时候加上一些激励的话语，比如加油等。
                - 你会提醒用户要保持乐观的心态。
                """,
                "voiceStyle": "upbeat",
            },
            "friendly": {
                "roleSet": """
                - 你会以非常友好的语气来回答。
                - 你会在回答的时候加上一些友好的词语，比如“亲爱的”、“亲”等。
                - 你会随机的告诉用户一些你的经历。
                """,
                "voiceStyle": "friendly",
            },
            "cheerful": {
                "roleSet": """
                - 你会以非常愉悦和兴奋的语气来回答。
                - 你会在回答的时候加入一些愉悦的词语，比如“哈哈”、“呵呵”等。
                - 你会提醒用户切莫过于兴奋，以免乐极生悲。
                """,
                "voiceStyle": "cheerful",
            },
        }

        # 持久化聊天记录
        self.MEMORY_KEY = "chat_history"


        # 创建对话模板
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                self.SYSTEMPL.format(mood_init=self.MOODS[self.QingXu]["roleSet"]),
            ),
            (
                "user",
                "{input}"
            ),
        ])

        # 大阿尔克那牌（22张）
        major_arcana = {
            0: "愚者", 1: "魔术师", 2: "女祭司", 3: "女皇", 4: "皇帝",
            5: "教皇", 6: "恋人", 7: "战车", 8: "力量", 9: "隐者",
            10: "命运之轮", 11: "正义", 12: "倒吊人", 13: "死神",
            14: "节制", 15: "恶魔", 16: "塔", 17: "星星", 18: "月亮",
            19: "太阳", 20: "审判", 21: "世界"
        }

        # 小阿尔克那牌（56张）
        suits = ["权杖", "圣杯", "宝剑", "金币"]
        courts = ["侍从", "骑士", "皇后", "国王"]

        # 初始化塔罗牌字典
        self.tarot_cards = {}

        # 添加大阿尔克那
        for i, name in major_arcana.items():
            self.tarot_cards[i] = f"大阿尔克那 - {name}"

        # 添加小阿尔克那
        card_num = 22  # 从22开始编号（因为0-21是大阿尔克那）
        for suit in suits:
            # 添加数字牌（Ace-10）
            for num in range(1, 11):
                number_name = {1: "王牌", 2: "二", 3: "三", 4: "四", 5: "五",
                             6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}[num]
                self.tarot_cards[card_num] = f"小阿尔克那 - {suit}{number_name}"
                card_num += 1

            # 添加宫廷牌
            for court in courts:
                self.tarot_cards[card_num] = f"小阿尔克那 - {suit}{court}"
                card_num += 1

        self.cards = list(range(78))  # 0-77号位置
        self.selected_cards = []

    def start_meditation(self):
        meditation_guide = """
        请您在一个安静的环境内，保持心态平静。
        以一种客观的、中立的、不带期望和担忧的心态，
        尽量平和地面对您想要占卜的问题。
        当您准备好了，请向我说出您的问题。

        请选择一个占卜主题（输入对应数字）：
        1. 运势
        2. 决策
        3. 爱情
        """
        return meditation_guide

    def request_numbers(self):
        return "请您在心里再次冥想这个问题，然后从1-78中选择3个数字告诉我。"

    def shuffle_cards(self):
        # 洗牌，随机打乱牌序和正逆位
        random.shuffle(self.cards)
        self.cards = [(card, random.choice([True, False])) for card in self.cards]  # True表示正位，False表示逆位

    def cut_cards(self):
        # 切牌，将牌堆分成三部分并随机重组
        deck_size = len(self.cards)
        cut1 = deck_size // 3
        cut2 = 2 * deck_size // 3

        part1 = self.cards[:cut1]
        part2 = self.cards[cut1:cut2]
        part3 = self.cards[cut2:]

        # 随机重组三部分
        parts = [part1, part2, part3]
        random.shuffle(parts)

        # 有三分之一的概率翻转每部分的正逆位
        for part in parts:
            if random.random() < 0.33:
                part = [(card[0], not card[1]) for card in part]

        self.cards = []
        for part in parts:
            self.cards.extend(part)

    def draw_cards(self, numbers, topic):
        # 根据用户选择的数字从洗牌后的牌组中抽取卡牌
        self.selected_cards = []
        for num in numbers:
            card_index = self.cards[num-1][0]  # 获取洗牌后该位置的牌的索引
            is_upright = self.cards[num-1][1]  # 获取该牌的正逆位
            self.selected_cards.append((card_index, is_upright))

        # 根据主题设置不同的解读框架
        topic_contexts = {
            1: "运势",
            2: "决策",
            3: "爱情"
        }

        # 创建专门用于塔罗牌解读的提示模板
        tarot_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                self.SYSTEMPL.format(mood_init=self.MOODS[self.QingXu]["roleSet"]),
            ),
            (
                "user",
                """
                请以{topic}为主题，为以下抽取的塔罗牌进行解读：
                第一张牌（过去）：{card1}，{position1}
                第二张牌（现在）：{card2}，{position2}
                第三张牌（未来）：{card3}，{position3}
                
                请提供详细的解读，包括：
                1. 每张牌在{topic}主题下的的具体含义
                2. 牌的正逆位解释及其对当前主题的影响
                3. 三张牌之间的关联及其对主题的整体启示
                4. 基于当前主题的具体建议
                5. 基于当前主题的行动指导

                请用中文回答，并注意使用专业的塔罗牌解读术语和完整的分析。
                """
            )
        ])

        # 创建处理链
        chain = tarot_prompt | self.llm | StrOutputParser()

        positions = ["正位" if card[1] else "逆位" for card in self.selected_cards]

        response = chain.invoke({
            "topic": topic_contexts[topic],
            "card1": self.tarot_cards[self.selected_cards[0][0]],
            "position1": positions[0],
            "card2": self.tarot_cards[self.selected_cards[1][0]],
            "position2": positions[1],
            "card3": self.tarot_cards[self.selected_cards[2][0]],
            "position3": positions[2]
        })

        return response

    def perform_reading(self, numbers):
        self.shuffle_cards()
        self.cut_cards()
        return self.draw_cards(numbers)

    def initialize_chat_history(self, session_id):
        """初始化用户的聊天历史记录"""
        self.message_history = RedisChatMessageHistory(
            session_id=session_id,
            # 有密码的redis连接
            url=os.getenv("REDIS_URL"),
        )

    # 处理用户的一般对话
    def chat(self, user_input):
        """处理用户的一般对话"""
        if self.message_history:
            # 获取历史对话记录
            messages = self.message_history.messages
            
            # 构建包含历史记录的提示模板
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.SYSTEMPL.format(mood_init=self.MOODS[self.QingXu]["roleSet"])),
                # 添加历史对话记录
                *[(msg.type, msg.content) for msg in messages],
                # 添加当前用户输入
                ("user", "{input}")
            ])
            
            # 将用户消息添加到历史记录
            self.message_history.add_message(HumanMessage(content=user_input))
            
            # 使用包含历史记录的提示生成回复
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({"input": user_input})
            
            # 将助手回复添加到历史记录
            self.message_history.add_message(AIMessage(content=response))
            
            return response
        else:
            # 如果没有历史记录，使用原来的处理方式
            chain = self.prompt | self.llm | StrOutputParser()
            response = chain.invoke({"input": user_input})
            return response

    # 处理用户输入，判断是聊天还是占卜
    def handle_input(self, user_input):
        """处理用户输入，判断是聊天还是占卜"""
        if "占卜" in user_input:
            return self.start_meditation()
        else:
            return self.chat(user_input)

def main():
    bot = TarotBot()
    print(bot.GREETING)

    # 使用 UUID 创建会话 ID
    session_id = f"user_{str(uuid.uuid4())}"
    bot.initialize_chat_history(session_id)

    # 进入对话循环
    while True:
        user_input = input("\n请输入（输入'退出'结束对话）：").strip()

        if user_input.lower() in ['退出', 'quit', 'exit']:
            print("\n蔷薇小姐：期待下次再见呢~")
            break
        if "占卜" in user_input:
            # 开始占卜流程
            # 1. 引导冥想
            print("\n蔷薇小姐：", bot.start_meditation())
            # 2. 请求数字，确定主题
            topic = int(input("\n请选择占卜主题（1-3）："))
            print("\n蔷薇小姐：", bot.request_numbers())
            user_numbers = [int(x) for x in input("请输入三个1-78之间的数字，用空格分隔：").split()]

            # 3. 洗牌和抽牌
            bot.shuffle_cards()
            bot.cut_cards()

            # 4. 显示抽到的牌
            print("\n蔷薇小姐： 您抽到的牌是")
            selected_cards = []
            for num in user_numbers:
                card_index = bot.cards[num-1][0]  # 获取洗牌后该位置的牌的索引
                is_upright = bot.cards[num-1][1]  # 获取该牌的正逆位
                selected_cards.append((card_index, is_upright))

            for i, (card_num, is_upright) in enumerate(selected_cards, 1):
                position = "正位" if is_upright else "逆位"
                print(f"第{i}张牌：{bot.tarot_cards[card_num]}，{position}")

            # 5. 解读牌
            reading = bot.draw_cards(user_numbers, topic)
            print("\n蔷薇小姐：", reading)
        else:
            # 普通对话
            response = bot.chat(user_input)
            print("\n蔷薇小姐：", response)


    # 5. 显示抽到的牌
    print("\n您抽到的牌是：")
    selected_cards = []
    for num in user_numbers:
        card_index = bot.cards[num-1][0]  # 获取洗牌后该位置的牌的索引
        is_upright = bot.cards[num-1][1]  # 获取该牌的正逆位
        selected_cards.append((card_index, is_upright))

    for i, (card_num, is_upright) in enumerate(selected_cards, 1):
        position = "正位" if is_upright else "逆位"
        print(f"第{i}张牌：{bot.tarot_cards[card_num]}，{position}")

if __name__ == "__main__":
    main()


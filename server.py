from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import random
import os

# 设置OpenAI API密钥和基础URL
os.environ["OPENAI_API_KEY"] = ""  # 请替换为您的API密钥
os.environ["OPENAI_API_BASE"] = ""  # 请替换为您的API基础URL

class TarotBot:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4o", 
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE")
        )
        
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
        
        template = """
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
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
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

def main():
    bot = TarotBot()
    
    # 1. 引导冥想
    print(bot.start_meditation())
    topic = int(input("请选择占卜主题（1-3）："))
    
    # 2. 请求数字
    print(bot.request_numbers())
    
    # 3. 假设用户输入了三个数字
    user_numbers = [int(x) for x in input("请输入三个1-78之间的数字，用空格分隔：").split()]

     # 4. 进行洗牌和切牌
    bot.shuffle_cards()
    bot.cut_cards()
    
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
    
    print("\n塔罗牌解读：")
    reading = bot.draw_cards(user_numbers, topic)
    print(reading)


if __name__ == "__main__":
    main()


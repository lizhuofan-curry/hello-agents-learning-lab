# 用于正则表达式匹配
# 完成判断用户说的是工作，学习还是爱好
# 提取用户句子中的内容，识别姓名，年龄，职业
# 替换代词
import re
# 用于随机选择回答，让机器人不会每次都说同一句话
import random

# 这里的rules是一个列表，列表中的每个元素又是一个二元组
# 也就是匹配模式 + 对应的回答列表
rules = [
    # 工作
    (
        # (?:as|in) 表示匹配 as 或者 in
        r'I work (?:as|in) (.*)',
        [
            "How do you feel about working as/in {0}?",
            "What do you like most about your work in {0}?",
            "Does working in {0} make you feel fulfilled?"
        ]
    ),

    # 学习
    (
        r'I am studying (.*)',
        [
            "What interests you about {0}?",
            "What is the most difficult part of studying {0}?",
            "How long have you been studying {0}?"
        ]
    ),

    # 爱好
    (
        r'I like (.*)',
        [
            "Why do you like {0}?",
            "How often do you spend time on {0}?",
            "What makes {0} enjoyable for you?"
        ]
    ),

    # 情绪
    (
        r'I feel (.*)',
        [
            "Why do you feel {0}?",
            "What usually makes you feel {0}?",
            "How long have you felt {0}?"
        ]
    ),

    # 需求
    (
        r'I need (.*)',
        [
            "Why do you need {0}?",
            "Would getting {0} really help you?",
            "What would happen if you did not get {0}?"
        ]
    ),

    # 家庭
    (
        # \b 表示单词边界，它不强求mother前后都有空格
        r'.*\bmother\b.*',
        [
            "Tell me more about your mother.",
            "How do you feel about your mother?"
        ]
    ),

    (
        r'.*\bfather\b.*',
        [
            "Tell me more about your father.",
            "How do you feel about your father?"
        ]
    ),

    # 兜底规则必须放在最后
    (
        r'.*',
        [
            "Please tell me more.",
            "Can you elaborate on that?",
            "What does that mean to you?"
        ]
    )
]

# 代词转换表
pronoun_swap = {
    "i": "you",
    "you": "I",
    "me": "you",
    "my": "your",
    "your": "my",
    "am": "are",
    "are": "am",
    "mine": "yours",
    "yours": "mine"
}


def swap_pronouns(phrase):
    """转换第一、第二人称代词。"""

    def replace_word(match):
        word = match.group(0).lower()
        return pronoun_swap.get(word, word)
    # 先用正则表达式寻找这些单词
    # 再把匹配对象传给 replace_word
    return re.sub(
        r"\b(i|you|me|my|your|am|are|mine|yours)\b",
        replace_word,
        phrase,
        flags=re.IGNORECASE
    )

# 保存用户信息
# uer_input 当前用户输入
# memory    保存历史信息的字典
def remember_information(user_input, memory):
    """从用户输入中提取姓名、年龄和职业。"""

    name_match = re.search(
        r'my name is ([A-Za-z]+)',
        user_input,
        re.IGNORECASE
    )

    if name_match:
        memory["name"] = name_match.group(1)
        return f"Nice to meet you, {memory['name']}."

    age_match = re.search(
        # \d 表示数字  {1，3} 表示连续出现1~3次
        r'I am (\d{1,3}) years old',
        user_input,
        re.IGNORECASE
    )

    if age_match:
        memory["age"] = age_match.group(1)
        return f"I will remember that you are {memory['age']} years old."

    job_match = re.search(
        # (?:an?) 表示可以匹配 a an 或者完全不出现
        # n? 表示字母 n 可以出现零次或者一次
        # [.!?]?$ 表示句子结尾可以有一个 . ! ?,也可以没有标点
        r'I work as (?:an? )?([A-Za-z ]+?)[.!?]?$',
        user_input,
        re.IGNORECASE
    )

    if job_match:
        memory["job"] = job_match.group(1).strip()
        return f"I will remember that you work as {memory['job']}."

    return None


def answer_memory_question(user_input, memory):
    """回答与已保存信息有关的问题。"""

    if re.search(r'what(?:\'s| is) my name', user_input, re.IGNORECASE):
        if "name" in memory:
            return f"Your name is {memory['name']}."
        return "You have not told me your name yet."

    if re.search(r'how old am I', user_input, re.IGNORECASE):
        if "age" in memory:
            return f"You are {memory['age']} years old."
        return "You have not told me your age yet."

    if re.search(
        r'what(?:\'s| is) my (?:job|occupation)',
        user_input,
        re.IGNORECASE
    ):
        if "job" in memory:
            return f"You work as {memory['job']}."
        return "You have not told me your occupation yet."

    return None


def respond(user_input, memory):
    # 先判断用户是否在询问历史信息
    memory_answer = answer_memory_question(user_input, memory)

    if memory_answer:
        return memory_answer

    # 再尝试保存用户新提供的信息
    remember_answer = remember_information(user_input, memory)

    if remember_answer:
        return remember_answer

    # 最后进行普通的规则匹配
    for pattern, responses in rules:
        match = re.search(pattern, user_input, re.IGNORECASE)

        if match:
            captured_group = match.group(1) if match.groups() else ""
            swapped_group = swap_pronouns(captured_group)
            response = random.choice(responses).format(swapped_group)

            # 在普通回答中引用姓名
            if "name" in memory and random.random() < 0.3:
                response = f"{memory['name']}, {response}"

            return response

    return "Please tell me more."


if __name__ == "__main__":
    memory = {}

    print("Therapist: Hello! How can I help you today?")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Therapist: Goodbye.")
            break

        print("Therapist:", respond(user_input, memory))
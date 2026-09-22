# 这是一个由阿里巴巴达摩院开源的拥有约 5 亿参数的对话模型
# 它体积小，性能优异，非常适合入门学习和本地部署

# 在 transformers 库中，我们通常使用 AutoModelForCausalLM 和 AutoTokenizer
# 这两个类来自动加载与模型匹配的权重和分词器
# 下面这段代码会自动从 Hugging Face Hub 下载所需的模型文件和分词器配置
# Hugging Face 在这段程序里面主要充当了"模型仓库"，不是远程推理服务器

import os

import torch
from transformers import AutoModelForCausalLM , AutoTokenizer

# 指定模型 ID
# 它不是普通模型名字，实际上它是 Hugging Face Hub 上一个模型仓库的 Repository ID
# Qwen / Qwen1.5-0.5B-Chat
# 组织名    仓库名
# 在电脑上安装 transformers 的时候，同时会使用另一个非常重要的 Python 库 huggingface_hub
# 代码 -> transformers -> huggingface_hub -> HTTPS 网络请求 -> huggingface.co

# Qwen1.5 是 Qwen2 的 beta版本
model_id = 'Qwen/Qwen1.5-0.5B-Chat'

# Hugging Face 模型下载位置
cache_dir = os.getenv('QWEN_CACHE_DIR')
print(f'模型缓存目录: {cache_dir}')

# 设置设备，优先使用GPU
device =  'cuda' if torch.cuda.is_available() else 'cpu'
print(f'Using device :{device}')

# 加载分词器
# 下载描述这个 tokenizer 的文件，具体文件会因模型而异
# auto 根据配置自动选择正确实现
tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    cache_dir=cache_dir,
)

# 加载模型，并将其移动到指定设备
# 这是在下载模型参数，这里面有一个非常核心的东西 config.json
# 里面记录了模型参数相关信息 如：这是什么模型，隐藏层大小多少，用的什么架构
# AutoModelForCausalLM 用于因果语言模型任务，非常适合自回归生成模型
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    cache_dir=cache_dir,
).to(device)

print('模型和分词器加载完成！')

# 我们来创建一个对话提示，Qwen1.5-Chat 模型遵循特定的对话模板。
# 然后，可以使用上一步加载的 tokenizer 将文本提示转化为模型能理解的数字ID (即 token ID)

# 准备对话输入
# Qwen 本质上还是 下一个Token 预测器
# 它根本不认识python字典里面的内容，所以必须把message翻译成Qwen训练时见过的文本格式
messages = [
    {'role' : 'system', 'content' : 'You are a helpful assistant.'},
    {'role' : 'user' , 'content': '你好，你能为我做什么。'}
]

# 使用分词器的模板格式化输入
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True  # Assistant 回答从这里开始
)

# 编码输入文本 [text] 表示一个batch,里面有一条文本，所以B=1
# pt 意思就是 pytorch
model_inputs = tokenizer([text],return_tensors='pt').to(device)

print('编码后的输入文本:')
print(model_inputs)

# 现在可以调用模型的 generate 方法来生成回答了
# 模型会输出一系列Token ID ,这代表它的回答
# 最后，需要使用分词器的 decode() 方法，将这些数字 ID 翻译回人类可以阅读的文本

# 使用模型生成回答
# max_new_tokens 控制了模型最多能生成多少个新的tokens
generated_ids = model.generate(
    model_inputs.input_ids,
    max_new_tokens = 512
)

#  将生成的 Token ID 截取掉输入部分
# model.generate 返回的通常不只有 模型回答，而是 原始输入 + 模型回答
# 所以从 len(input_ids) 开始截取
# 这样我们只解码模型新生成的部分
generated_ids = [
    output_ids[len(input_ids):] for input_ids,output_ids in zip(model_inputs.input_ids,generated_ids)
]

# 解码生成的 Token ID
# skip_special_tokens 就是不把模型控制结构打印出来
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print('\n模型的回答:')
print(response)

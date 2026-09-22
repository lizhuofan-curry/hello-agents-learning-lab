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
# messages = [
#     {'role' : 'system', 'content' : 'You are a helpful assistant.'},
#     {'role' : 'user' , 'content': '中国的首都是'}
# ]

# 使用分词器的模板格式化输入
# text = tokenizer.apply_chat_template(
#     messages,
#     tokenize=False,
#     add_generation_prompt=True  # Assistant 回答从这里开始
# )

text = '中国的首都是'
model_inputs = tokenizer(
    text,
    return_tensors='pt',
).to(device)

# 编码输入文本 [text] 表示一个batch,里面有一条文本，所以B=1
# pt 意思就是 pytorch
model_inputs = tokenizer([text],return_tensors='pt').to(device)

print("\n===== Chat Template 后的文本 =====")
print(text)

print("\n===== input_ids =====")
print(model_inputs.input_ids)

print("\ninput_ids 的形状：")
print(model_inputs.input_ids.shape)

print("\n===== 对应的 Tokens =====")
tokens = tokenizer.convert_ids_to_tokens(
    model_inputs.input_ids[0]
)
print(tokens)

print('\n===== 每个 Token 的真实解码效果 =====')
for i,token_id in enumerate(model_inputs.input_ids[0]):
    token_id = token_id.item()
    decoded = tokenizer.decode([token_id])
    print(
        f'位置{i:2d} |'
        f'ID={token_id:<8} |'
        f'内容={repr(decoded)}'
    )
print('编码后的输入文本:')
print(model_inputs)

# 现在可以调用模型的 generate 方法来生成回答了
# 模型会输出一系列Token ID ,这代表它的回答
# 最后，需要使用分词器的 decode() 方法，将这些数字 ID 翻译回人类可以阅读的文本

# 使用模型生成回答
# max_new_tokens 控制了模型最多能生成多少个新的tokens
# generated_ids = model.generate(
#     model_inputs.input_ids,
#     max_new_tokens = 512
# )

# 告诉pytorch: 这里只推理，不训练
with torch.no_grad():
    outputs = model(
        input_ids = model_inputs.input_ids,
        attention_mask = model_inputs.attention_mask,
    )
    logits = outputs.logits
    print('\n===== logits 形状 ====')
    print(logits.shape)

    # 拿到最后一个位置的 logits
    # 取batch中第0条文本，-1取序列最后一个位置，:取这个位置对于整个词表的所有分数
    next_token_logits = logits[0,-1,:]

    print("\n===== 下一个 Token 的 logits =====")
    print(next_token_logits.shape)

    temperature = 1.0
    top_p = 0.9

    # 手动做 Softmax + Temperature
    proabilities = torch.softmax(
        next_token_logits / temperature,
        dim = -1
    )

    print('\n所有概率之和：')
    print(proabilities.sum().item())

    # 将整个词表按照概率从高到低排序
    # Top-p 定义为从概率最高的 Token 开始累加
    sorted_porbs,sorted_ids = torch.sort(
        proabilities,
        descending = True,
    )

    # 计算累计概率
    cumulative_probs = torch.cumsum(
        sorted_porbs,
        dim = -1
    )

    print('\n===== 概率最高的前 15 个 Token ====')
    for i in range(15):
        token_id = sorted_ids[i].item()

        token_text = tokenizer.decode([token_id])

        print(f'{i+1:2d}.'
              f'Token={repr(token_text):<15}'
              f'概率={sorted_porbs[i]:.4%}'
              f'累计概率={cumulative_probs[i].item():.4%}'
              )

    # 找出累计概率超过 top_p 的位置
    # 注意： 我们要保留第一个让累计概率达到/超过 top_p 的token
    # 这里返回的是一个布尔数组 [false,false,true,true .....]
    sorted_indices_to_remove = (cumulative_probs > top_p)

    # 向右移动一位
    # 这样第一个超过 top_p 的token 仍然会被保留
    '''
    原来 [False,False,False,True,True]
    sorted_indices_to_move[:-1] 表示从开头取到倒数第二个 得到 [False,False,False,True]
    注意上面的最后一个 True 没取
    [1:] 表示从下标 1 开始一直到最后 指的是后四个位置 1，2，3，4
    这样就实现右移了
    '''
    sorted_indices_to_remove[1:] = (sorted_indices_to_remove[:-1]).clone()
    sorted_indices_to_remove[0] = False

    # 得到真正需要保留的 Token
    # 这里 ~ 对布尔值表示取反，删除掩码 取反 保留掩码
    keep_mask = ~sorted_indices_to_remove

    # 很常见的布尔索引
    top_p_probs = sorted_porbs[keep_mask]
    top_p_ids = sorted_ids[keep_mask]

    print( f'\n===== Top-p = {top_p} 筛选结果 =====')
    print(f'最终保留 Token 数量：{len(top_p_ids)}')
    print( f'重新归一化前概率和：'
           f'{top_p_probs.sum().item():.4%}')

    # 重新归一化
    top_p_probs = top_p_probs / top_p_probs.sum()
    print(f'重新归一化后的概率和：'f'{top_p_probs.sum().item():.4%}')

    # 打印最终候选 Token
    print('\n===== Top-p 最终候选集合 =======')
    for token_id,prob in zip(top_p_ids,top_p_probs):
        token_text = tokenizer.decode([token_id.item()])
        print(repr(token_text),f'{prob.item():.4%}')

    # 按概率真正随机采样一个 Token
    sample_index = torch.multinomial(
        top_p_probs,
        num_samples=1
    )

    next_token_id = top_p_ids[sample_index]


    next_token = tokenizer.decode([next_token_id.item()])

    print('\n本次真正采样出的 Token：')
    # 用 repr() 是为了调试和观察字符串的真实内容
    # print更像 把字符串按照用户应该看到的方式展示
    # repr() 更像 把这个字符串在程序里的真实样子给我看看
    print(repr(next_token))




#  将生成的 Token ID 截取掉输入部分
# model.generate 返回的通常不只有 模型回答，而是 原始输入 + 模型回答
# 所以从 len(input_ids) 开始截取
# 这样我们只解码模型新生成的部分
# generated_ids = [
#     output_ids[len(input_ids):] for input_ids,output_ids in zip(model_inputs.input_ids,generated_ids)
# ]
#
# # 解码生成的 Token ID
# # skip_special_tokens 就是不把模型控制结构打印出来
# response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
#
# print('\n模型的回答:')
# print(response)

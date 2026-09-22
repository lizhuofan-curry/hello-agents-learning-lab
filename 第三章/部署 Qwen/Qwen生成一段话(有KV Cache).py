# 这是一个由阿里巴巴达摩院开源的拥有约 5 亿参数的对话模型
# 它体积小，性能优异，非常适合入门学习和本地部署

# 在 transformers 库中，我们通常使用 AutoModelForCausalLM 和 AutoTokenizer
# 这两个类来自动加载与模型匹配的权重和分词器
# 下面这段代码会自动从 Hugging Face Hub 下载所需的模型文件和分词器配置
# Hugging Face 在这段程序里面主要充当了"模型仓库"，不是远程推理服务器

import os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

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
device = 'cuda' if torch.cuda.is_available() else 'cpu'
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


# 把 Top-p 抽样单独做成一个函数
# Top-p 控制拿到 logits 后怎么选择 Token
# KV cahce 控制 Transformer 怎么高效地算出 logits
def top_p_sample(next_token_logits, temperature=1.0, top_p=0.9):
    '''它只负责这一轮的 logits , 返回抽中的 Token ID'''
    # -----------------------------
    # 1. Temperature + Softmax
    # -----------------------------

    probabilities = torch.softmax(
        next_token_logits.float() / temperature,
        dim=-1
    )

    # -----------------------------
    # 2. 按概率从大到小排序
    # -----------------------------

    sorted_probs, sorted_ids = torch.sort(
        probabilities,
        descending=True
    )

    # -----------------------------
    # 3. 计算累计概率
    # -----------------------------

    cumulative_probs = torch.cumsum(
        sorted_probs,
        dim=-1
    )

    # -----------------------------
    # 4. Top-p 筛选
    # -----------------------------

    sorted_indices_to_remove = (
            cumulative_probs > top_p
    )

    # 第一个让累计概率超过 top_p 的 Token
    # 仍然需要保留
    sorted_indices_to_remove[1:] = (
        sorted_indices_to_remove[:-1]
    ).clone()

    sorted_indices_to_remove[0] = False

    # 得到保留掩码
    keep_mask = ~sorted_indices_to_remove

    # 保留下来的概率与 Token ID
    top_p_probs = sorted_probs[keep_mask]
    top_p_ids = sorted_ids[keep_mask]

    # -----------------------------
    # 5. 重新归一化
    # -----------------------------

    top_p_probs = (
            top_p_probs / top_p_probs.sum()
    )

    # -----------------------------
    # 6. Sampling
    # -----------------------------

    sample_index = torch.multinomial(
        top_p_probs,
        num_samples=1
    )

    next_token_id = top_p_ids[
        sample_index
    ]

    return next_token_id


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

inputs_ids = model_inputs.input_ids
attention_mask = model_inputs.attention_mask

# 手动实现自回归文本生成

# 用来保存最终生成结果
generated_tokens_ids = []

# KV Cache 一开始还没有任何 KV Cache
past_key_values = None

# 当前真正需要送进模型的 Token
# inputs_ids 为到目前为止的完整 Token 序列
# current_input_ids 为这一轮真正需要送进 Transformer 计算的 Token

# 第一轮需要把完整的 Prompt 送进去
current_input_ids = inputs_ids

# 先设置最多生成多少 Token
max_new_tokens = 50

# 开始最核心的循环
for step in range(max_new_tokens):
    print( f"\n===== 第 {step + 1} 轮 =====")
    print("完整 input_ids.shape：", inputs_ids.shape)
    print("本轮真正输入模型的 current_input_ids.shape：",current_input_ids.shape)
    print("attention_mask.shape：", attention_mask.shape)

    # transformer forward
    with torch.no_grad():

        outputs = model(
            input_ids = current_input_ids,
            attention_mask = attention_mask,   # 模型需要知道 整个上下文中哪些 Key/Value 是有效内容，尤其是句子长度不一样的时候
            past_key_values = past_key_values, # 如果以前已经缓存过 K,V 就把它们交给模型继续使用
            use_cache = True,   # 这轮 Forward 算完以后，请把新的 K,V 也返回给我
        )

        print('output.logits.shape:',outputs.logits.shape)

        # 保存/更新 KV Cache
        # 这一步自动将新加的 k,v append了，模型内部自己完成的
        past_key_values = outputs.past_key_values

        # 取最后位置的 logits
        # 得到下一个预测 Token 的原始 logits
        next_token_logits = outputs.logits[0,-1,:]


        # Top-p Sampling
        next_token_id = top_p_sample(
            next_token_logits,
            temperature= 1.0,
            top_p=0.9
        )

        next_token_text = tokenizer.decode(
            [next_token_id.item()]
        )

        print(
            f"生成 Token :"
            f"Token ID={next_token_id.item():<8} "
            f"Token={repr(next_token_text)}"
        )

        generated_tokens_ids.append(next_token_id.item())

        # 语言模型有一个 EOS Token (end of Sequence) 判断序列结束
        if next_token_id.item() == tokenizer.eos_token_id :
            print('遇到 EOS ,停止生成')
            break

        # 最关键的一步 把新 Token  拼回 inputs——ids  保存完整序列
        # 这是自回归生成最核心的动作
        inputs_ids = torch.cat([inputs_ids,next_token_id.view(1,1)],dim=-1)


        # attention_mask 也必须跟着变
        # 原来 [1，1，1] 代表三个 Token 都有效
        # 现在新增北京 所以应该变成 [1,1,1,1]
        new_mask = torch.ones(
            (attention_mask.size(0),1),
            dtype = attention_mask.dtype,
            device = attention_mask.device,
        )

        attention_mask = torch.cat([attention_mask,new_mask],dim=-1)

        # 下一轮只输入刚生成的 Token
        current_input_ids  = next_token_id.view(1,1)

# 最后把生成的 Token 一次性解码
generated_text = tokenizer.decode(
    generated_tokens_ids,
    skip_special_tokens=True,
)
print('\n====== 最终生成文本 ======')
# 之前是在研究每一个token，所以必须要加上repr
# 现在输出的是人类真正阅读的最终答案，所以不需要 repr()
print(generated_text)


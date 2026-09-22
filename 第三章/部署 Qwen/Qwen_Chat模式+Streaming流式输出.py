import os

import torch

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer
)

# ==========================================
# 1. 加载 Qwen
# ==========================================

model_id = "Qwen/Qwen1.5-0.5B-Chat"

cache_dir = os.getenv("QWEN_CACHE_DIR")


# 优先使用 GPU
device = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print("Using device:", device)

# 加载 tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    cache_dir=cache_dir
)


# 加载模型
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    cache_dir=cache_dir
).to(device)


# 设置推理模式
model.eval()


print("模型和分词器加载完成！")

# ==========================================
# 2. Top-p Sampling
# ==========================================

def top_p_sample(
        next_token_logits,
        temperature=1.0,
        top_p=0.9
):

    # --------------------------------------
    # 1. Temperature + Softmax
    # --------------------------------------

    probabilities = torch.softmax(
        next_token_logits.float() / temperature,
        dim=-1
    )


    # --------------------------------------
    # 2. 概率从高到低排序
    # --------------------------------------

    sorted_probs, sorted_ids = torch.sort(
        probabilities,
        descending=True
    )


    # --------------------------------------
    # 3. 计算累计概率
    # --------------------------------------

    cumulative_probs = torch.cumsum(
        sorted_probs,
        dim=-1
    )


    # --------------------------------------
    # 4. Top-p 筛选
    # --------------------------------------

    sorted_indices_to_remove = (
        cumulative_probs > top_p
    )


    # 第一个让累计概率超过 top_p 的 Token
    # 仍然保留
    sorted_indices_to_remove[1:] = (
        sorted_indices_to_remove[:-1]
    ).clone()

    sorted_indices_to_remove[0] = False


    # --------------------------------------
    # 5. 得到保留的 Token
    # --------------------------------------

    keep_mask = ~sorted_indices_to_remove

    top_p_probs = sorted_probs[
        keep_mask
    ]

    top_p_ids = sorted_ids[
        keep_mask
    ]


    # --------------------------------------
    # 6. 重新归一化
    # --------------------------------------

    top_p_probs = (
        top_p_probs
        /
        top_p_probs.sum()
    )


    # --------------------------------------
    # 7. 真正 Sampling
    # --------------------------------------

    sample_index = torch.multinomial(
        top_p_probs,
        num_samples=1
    )


    next_token_id = top_p_ids[
        sample_index
    ]


    return next_token_id

# ==========================================
# 3. 初始化对话历史
# ==========================================

# system 只需要放一次
messages = [
    {
        "role": "system",
        "content": (
            "你是一个对话助手。"
            "请严格区分 user 和 assistant 的身份。"
            "user 表示与你对话的用户，assistant 表示你自己。"
            "当用户提到“我”时，通常指用户本人，而不是你。"
            "回答关于之前对话的问题时，请根据完整聊天历史回答。"
        )
    }
]


# 每次回答最多生成多少个新 Token
max_new_tokens = 100


print("\n===== Qwen 多轮聊天 =====")
print("输入 exit / quit / 退出 可以结束程序")


# ==========================================
# 4. 多轮聊天
# ==========================================

while True:

    # --------------------------------------
    # 1. 获取用户输入
    # --------------------------------------

    user_input = input("\n你：").strip()


    # --------------------------------------
    # 2. 判断用户是否退出
    # --------------------------------------

    if user_input.lower() in {
        "exit",
        "quit",
        "退出"
    }:

        print("聊天结束。")

        break


    # 如果用户什么都没输入，就重新输入
    if not user_input:
        continue


    # --------------------------------------
    # 3. 把当前用户消息加入历史
    # --------------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # ======================================
    # 4. 将完整聊天历史转换为 Chat Template
    # ======================================

    print("\n===== 当前完整 messages =====")

    for message in messages:
        print(
            message["role"],
            ":",
            message["content"]
        )

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )


    # ======================================
    # 5. Tokenizer
    # ======================================

    model_inputs = tokenizer(
        text,
        return_tensors="pt"
    ).to(device)


    input_ids = model_inputs.input_ids

    attention_mask = (
        model_inputs.attention_mask
    )


    # ======================================
    # 6. 当前这一轮回答的 KV Cache
    # ======================================

    # 每一轮新的用户提问开始时，
    # 我们重新对完整聊天历史进行 Prefill
    past_key_values = None

    current_input_ids = input_ids


    # 保存本轮 Qwen 新生成的 Token
    generated_token_ids = []


    # Streaming 用
    previous_text = ""


    print(
        "Qwen：",
        end="",
        flush=True
    )


    # ======================================
    # 7. 自回归生成回答
    # ======================================

    for step in range(max_new_tokens):

        # ----------------------------------
        # Transformer Forward
        # ----------------------------------

        with torch.no_grad():

            outputs = model(
                input_ids=current_input_ids,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
                use_cache=True
            )


        # ----------------------------------
        # 更新 KV Cache
        # ----------------------------------

        past_key_values = (
            outputs.past_key_values
        )


        # ----------------------------------
        # 最后位置 logits
        # ----------------------------------

        next_token_logits = outputs.logits[
            0,
            -1,
            :
        ]


        # ----------------------------------
        # Temperature + Top-p + Sampling
        # ----------------------------------

        next_token_id = top_p_sample(
            next_token_logits,
            temperature=0.8,
            top_p=0.9
        )


        # 保存生成的 Token
        generated_token_ids.append(
            next_token_id.item()
        )


        # ----------------------------------
        # EOS：本轮回答结束
        # ----------------------------------

        if (
            next_token_id.item()
            == tokenizer.eos_token_id
        ):

            break


        # ==================================
        # Streaming 输出
        # ==================================

        # 将目前已经生成的所有 Token 解码
        current_text = tokenizer.decode(
            generated_token_ids,
            skip_special_tokens=True
        )


        # 只拿这一轮新增加的字符
        new_text = current_text[
            len(previous_text):
        ]


        # 立即打印
        print(
            new_text,
            end="",
            flush=True
        )


        # 记录目前已经显示过的文本
        previous_text = current_text


        # ----------------------------------
        # attention_mask 增加一个位置
        # ----------------------------------

        new_mask = torch.ones(
            (attention_mask.size(0), 1),
            dtype=attention_mask.dtype,
            device=attention_mask.device
        )


        attention_mask = torch.cat(
            [
                attention_mask,
                new_mask
            ],
            dim=-1
        )


        # ----------------------------------
        # 下一轮只输入刚生成的新 Token
        # ----------------------------------

        current_input_ids = (
            next_token_id.view(1, 1)
        )


    # 当前 Qwen 回答结束以后换行
    print()


    # ======================================
    # 8. 得到本轮完整回答
    # ======================================

    assistant_response = tokenizer.decode(
        generated_token_ids,
        skip_special_tokens=True
    ).strip()


    # ======================================
    # 9. 把 Qwen 的回答也加入聊天历史
    # ======================================

    messages.append(
        {
            "role": "assistant",
            "content": assistant_response
        }
    )

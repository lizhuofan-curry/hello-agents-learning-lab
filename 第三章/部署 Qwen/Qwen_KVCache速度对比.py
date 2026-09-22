import os
import time # 这里主要用 time.perf_counter() 计时，来比较运行速度
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 没有 KV Cache 的函数
def generate_without_kv_cache(
        model,
        input_ids,
        attention_mask,
        max_new_tokens=100
):

    # 复制一份，避免修改原始输入
    input_ids = input_ids.clone()
    attention_mask = attention_mask.clone()


    # -----------------------------
    # GPU 同步
    # -----------------------------
    if input_ids.is_cuda:
        torch.cuda.synchronize()


    start_time = time.perf_counter()


    # -----------------------------
    # 自回归生成
    # -----------------------------
    for step in range(max_new_tokens):

        with torch.no_grad():

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False
            )


        # 最后位置 logits
        next_token_logits = outputs.logits[
            0,
            -1,
            :
        ]


        # Greedy
        next_token_id = torch.argmax(
            next_token_logits,
            dim=-1
        ).view(1, 1)


        # -----------------------------
        # 新 Token 拼回完整 input_ids
        # -----------------------------
        input_ids = torch.cat(
            [
                input_ids,
                next_token_id
            ],
            dim=-1
        )


        # attention_mask 增加一个 1
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


    # GPU 真正执行完再停止计时
    if input_ids.is_cuda:
        torch.cuda.synchronize()


    end_time = time.perf_counter()


    return (
        input_ids,
        end_time - start_time
    )

# 有 KV Cache 的函数
def generate_with_kv_cache(
        model,
        input_ids,
        attention_mask,
        max_new_tokens=100
):

    # 完整序列
    full_input_ids = input_ids.clone()

    attention_mask = attention_mask.clone()


    # 一开始没有 Cache
    past_key_values = None


    # 第一轮完整 Prompt
    current_input_ids = input_ids


    if input_ids.is_cuda:
        torch.cuda.synchronize()


    start_time = time.perf_counter()


    for step in range(max_new_tokens):

        with torch.no_grad():

            outputs = model(
                input_ids=current_input_ids,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
                use_cache=True
            )


        # -----------------------------
        # 更新 KV Cache
        # -----------------------------
        past_key_values = (
            outputs.past_key_values
        )


        # 最后位置 logits
        next_token_logits = outputs.logits[
            0,
            -1,
            :
        ]


        # Greedy
        next_token_id = torch.argmax(
            next_token_logits,
            dim=-1
        ).view(1, 1)


        # -----------------------------
        # 完整 Token 序列依然保存
        # -----------------------------
        full_input_ids = torch.cat(
            [
                full_input_ids,
                next_token_id
            ],
            dim=-1
        )


        # attention_mask 增长
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


        # -----------------------------
        # 最关键：
        # 下一轮只计算新 Token
        # -----------------------------
        current_input_ids = next_token_id


    if input_ids.is_cuda:
        torch.cuda.synchronize()


    end_time = time.perf_counter()


    return (
        full_input_ids,
        end_time - start_time
    )

text = (
    "请详细介绍人工智能的发展历史、"
    "机器学习、深度学习以及大语言模型之间的关系，"
    "并分别说明它们的核心思想和主要应用。"
)*10

# ==========================================
# 1. 加载模型和分词器
# ==========================================

model_id = "Qwen/Qwen1.5-0.5B-Chat"

cache_dir = os.getenv("QWEN_CACHE_DIR")


# 优先使用 GPU
device = "cuda" if torch.cuda.is_available() else "cpu"

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


# 设置为推理模式
model.eval()

print("模型和分词器加载完成！")

# ==========================================
# 2. Tokenizer 编码 Prompt
# ==========================================

model_inputs = tokenizer(
    text,
    return_tensors="pt"
).to(device)


input_ids = model_inputs.input_ids

attention_mask = model_inputs.attention_mask


print(
    "\n初始 Prompt Token 数量：",
    input_ids.shape[1]
)

print(
    "input_ids.shape：",
    input_ids.shape
)

# ==========================================
# 3. 设置实验参数
# ==========================================

max_new_tokens = 500

# ==========================================
# 4. GPU 预热
# ==========================================

print("\n===== GPU 预热 =====")


_ = generate_with_kv_cache(
    model,
    input_ids,
    attention_mask,
    max_new_tokens=10
)


print("GPU 预热完成！")

# ==========================================
# 5. 无 KV Cache
# ==========================================

print("\n===== 无 KV Cache =====")


output_without_cache, time_without_cache = (
    generate_without_kv_cache(
        model,
        input_ids,
        attention_mask,
        max_new_tokens=max_new_tokens
    )
)


print(
    f"生成 {max_new_tokens} 个 Token 耗时："
    f"{time_without_cache:.4f} 秒"
)

# ==========================================
# 6. 有 KV Cache
# ==========================================

print("\n===== 有 KV Cache =====")


output_with_cache, time_with_cache = (
    generate_with_kv_cache(
        model,
        input_ids,
        attention_mask,
        max_new_tokens=max_new_tokens
    )
)


print(
    f"生成 {max_new_tokens} 个 Token 耗时："
    f"{time_with_cache:.4f} 秒"
)

# ==========================================
# 7. 计算速度
# ==========================================

speedup = (
    time_without_cache
    /
    time_with_cache
)


tokens_per_second_without_cache = (
    max_new_tokens
    /
    time_without_cache
)


tokens_per_second_with_cache = (
    max_new_tokens
    /
    time_with_cache
)


print("\n========== 最终结果 ==========")


print(
    f"无 KV Cache 耗时："
    f"{time_without_cache:.4f} 秒"
)


print(
    f"有 KV Cache 耗时："
    f"{time_with_cache:.4f} 秒"
)


print(
    f"\n无 KV Cache："
    f"{tokens_per_second_without_cache:.2f} Token/s"
)


print(
    f"有 KV Cache："
    f"{tokens_per_second_with_cache:.2f} Token/s"
)


print(
    f"\nKV Cache 加速倍数："
    f"{speedup:.2f}x"
)

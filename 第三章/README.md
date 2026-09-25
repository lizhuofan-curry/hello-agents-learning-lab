# 第三章｜从词频到语言模型

这一章先用很小的语料理解“下一个词”概率，再动手看 BPE 如何合并词元，最后进入 Qwen 本地推理、采样、流式输出和 KV Cache。小脚本与模型实验分开：可以只用标准库理解前半段，不必一上来就下载模型。

## 先做不需要模型的实验

| 文件 | 关注点 |
|---|---|
| [N-gram 模型.py](./N-gram%20模型.py) | 迷你语料里的 Bigram 计数与条件概率 |
| [简化版 BPE.py](./简化版%20BPE.py) | 相邻词元计数与逐步合并 |
| [BPE 文本分词.py](./BPE%20文本分词.py) | 更完整的 BPE 合并过程 |

```powershell
# 在仓库根目录，无需额外依赖
python ".\第三章\N-gram 模型.py"
python ".\第三章\简化版 BPE.py"
```

Bigram 示例是帮助理解计算步骤的教学口径；真实语言模型还会涉及语料边界、平滑、分词方案等选择。

## 再看本地 Qwen

[部署 Qwen](./部署%20Qwen/) 中的脚本分别演示单个 Token 预测、连续生成、Chat 模式、流式输出，以及有无 KV Cache 的对比。可以从 [Qwen1.5-0.5B-Chat.py](./部署%20Qwen/Qwen1.5-0.5B-Chat.py) 读起，再看 [KV Cache 速度对比](./部署%20Qwen/Qwen_KVCache速度对比.py)。

```powershell
uv sync --group chapter3
uv run --group chapter3 python ".\第三章\部署 Qwen\Qwen1.5-0.5B-Chat.py"
```

本地模型可能首次下载权重，耗时、磁盘空间和内存/显存需求取决于环境。`QWEN_CACHE_DIR` 可按需设置；部分演示是交互式的，运行前先看文件里的模型路径与输入循环。

[第三章课后习题](../notes/第三章/第三章的问题.md)延伸到 Transformer、Decoder-Only、幻觉、RAG 与论文阅读 Agent 设计。

[返回主页](../README.md) · [下一章：Agent 工作流](../第四章/README.md)

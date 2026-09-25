# 第一章｜让 Agent 跑出第一个闭环

这一章用一个旅行助手回答最朴素的问题：模型说“下一步查天气”，程序如何真的调用天气工具，再把结果交还给模型？我把重点放在 **Thought → Action → Observation → 下一步** 的循环，而不是把一次模型回复误当作完整 Agent。

## 代码入口

- [动手体验：5分钟实现第一个智能体.py](./动手体验：5分钟实现第一个智能体.py)：天气查询、Tavily 景点搜索、动作解析和最终回答都写在同一个脚本里，方便逐行追踪。
- [第一章课后习题](../notes/第一章/第一章的问题.md)：智能体定义、闭环、记忆、幻觉、循环上限与评价。

## 运行

在仓库根目录使用 PowerShell：

```powershell
uv sync --group chapter1
Copy-Item .env.example .env
# 编辑 .env：填写 LLM_API_KEY、LLM_MODEL_ID、LLM_BASE_URL、TAVILY_API_KEY
uv run --group chapter1 python ".\第一章\动手体验：5分钟实现第一个智能体.py"
```

脚本会访问模型、天气和搜索服务；服务可用性、额度与结果都可能变化。阅读时可以重点观察：模型输出的 Action 如何被解析，工具结果怎样成为下一轮的 Observation，以及格式不符合约定时会怎样。这里的文本动作解析是教学实现，不是可信任的通用工具执行沙箱。

[返回主页](../README.md) · [下一章：ELIZA](../第二章/README.md)

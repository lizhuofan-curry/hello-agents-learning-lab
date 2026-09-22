'''
假设我们拥有一个仅包含以下两句话的迷你语料库：datawhale agent learns, datawhale agent works。
我们的目标是：使用 Bigram (N=2) 模型，估算句子 datawhale agent learns 出现的概率。
根据 Bigram 的假设，我们每次会考察连续的两个词（即一个词对）。
'''

# 这里主要使用 collections.Counter
# Counter 可以统计每一种 Bigram 出现的次数
import collections

# 示例语料库，与上方案例讲解的语料库保持一致
corpus = 'datawhale agent learns datawhale agent works'
tokens = corpus.split()
total_tokens = len(tokens)

# ------ 第一步 ：计算 P (datawhale) -------
count_datawhale = tokens.count('datawhale')
p_datawhale = count_datawhale / total_tokens
print(f'第一步：P(datawhale) = {count_datawhale}/{total_tokens} = {p_datawhale:.3f}')

# ------- 第二步: 计算 P(agent | datawhale) -----------
# 先计算 bigrams 用于后续步骤
# 相当于先后移一个，然后组队
bigrams = zip(tokens,tokens[1:])
bigrams_count = collections.Counter(bigrams)
count_datawhale_agent = bigrams_count[('datawhale','agent')]
# count_已在第一步计算
p_agent_given_datawhale = count_datawhale_agent / count_datawhale
print(f'第二步:P(agent|datawhale) = {count_datawhale_agent} / {count_datawhale} = {p_agent_given_datawhale:.3f}')

# --------- 第三步 : 计算 P(learns|agent) --------
count_agent_learns = bigrams_count[('agent','learns')]
count_aegnt = tokens.count('agent')
p_learns_given_agent = count_agent_learns / count_aegnt
print(f'第三步 P(learns | agent) = {count_agent_learns} / {count_aegnt} = {p_learns_given_agent:.3f}')

# ---------- 最后：将概率连乘 ----------------
p_sentence = p_datawhale * p_agent_given_datawhale * p_learns_given_agent
print(f"最后:P('datawhale agent learns') = {p_datawhale:.3f} * {p_agent_given_datawhale:.3f} * {p_learns_given_agent:.3f} = {p_sentence:.3f}")
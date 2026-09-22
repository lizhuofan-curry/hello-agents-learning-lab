import re,collections

# 统计谁出现最多
def get_start(vocab):
    '''统计词元频率'''

    # 创建一个字典    pairs 用来统计相邻 token pair次数
    '''
    例如：
    （'u','g'） : 2
    ('u','n') : 2
    defaultdict(int)的好处就是 如果pairs[('u','n')]原来不存在，默认就是0，可以直接 +=1
    '''
    pairs = collections.defaultdict(int)

    # 因为vocab是字典，所有 .item 会同时拿 key 和 value
    for word,freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols)-1):
            pairs[symbols[i],symbols[i+1]] += freq
    return pairs

# 把出现最多的合起来
# 也就是 查找 + 替换机器
# 查找 vocab里面的 pair ,将里面分开的两部分合并
def merge_vocab(pair,v_in):
    '''合并词元对'''
    # 保存新版本
    v_out = {}
    # 先join(pair) 变成 ('u g') 不是 ('ug')
    # re.escape 是给正则表达式使用的安全处理
    bigram = re.escape(' '.join(pair))
    # 创建一个搜索规则，专门找完整的 u g
    # 正则这里只是帮我们精准定位token边界
    p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
    for word in v_in:
        w_out = p.sub(''.join(pair),word)
        v_out[w_out] = v_in[word]
    return v_out

# 准备语料库，每个词末尾加上</w>表示结束，并切好字符
vocab = {'h u g </w>': 1, 'p u g </w>' : 1, 'p u n </w>': 1,'b u n </w>': 1}
num_merges = 4 # 设置合并次数
for i in range(num_merges):
    pairs = get_start(vocab)
    if not pairs:
        break
    # 找到 value 最大的那个 key
    # pairs.get 相当于 ('h','u') -> 1 ('p','u') -> 2
    # 所以就是按照出现次数找最大的pair
    best = max(pairs,key=pairs.get)
    vocab = merge_vocab(best,vocab)
    print(f"第{i + 1}次合并: {best} -> {''.join(best)}")
    print(f"新词表（部分）: {list(vocab.keys())}")
    print("-" * 20)
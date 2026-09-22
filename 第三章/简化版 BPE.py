from collections import defaultdict


def count_pairs(vocab):

    pairs = defaultdict(int)

    for tokens, freq in vocab.items():

        for i in range(len(tokens) - 1):

            pair = (tokens[i], tokens[i + 1])

            pairs[pair] += freq

    return pairs


def merge_pair(best_pair, vocab):

    new_vocab = {}

    for tokens, freq in vocab.items():

        new_tokens = []

        i = 0

        while i < len(tokens):

            if (
                i < len(tokens) - 1
                and tokens[i] == best_pair[0]
                and tokens[i + 1] == best_pair[1]
            ):
                new_tokens.append(
                    tokens[i] + tokens[i + 1]
                )

                i += 2

            else:
                new_tokens.append(tokens[i])

                i += 1

        new_vocab[tuple(new_tokens)] = freq

    return new_vocab


vocab = {
    ('h', 'u', 'g'): 1,
    ('p', 'u', 'g'): 1,
    ('p', 'u', 'n'): 1,
    ('b', 'u', 'n'): 1
}


for round_num in range(4):

    pairs = count_pairs(vocab)

    best_pair = max(
        pairs,
        key=pairs.get
    )

    vocab = merge_pair(
        best_pair,
        vocab
    )

    print(best_pair)
    print(vocab)
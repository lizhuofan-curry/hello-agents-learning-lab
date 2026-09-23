#!/usr/bin/env python3
"""计算 1 到 100 所有整数之和，并打印结果。"""

def compute_sum(start: int = 1, end: int = 100) -> int:
    """计算从 start 到 end（包含两端）的所有整数之和。"""
    return sum(range(start, end + 1))

def main() -> None:
    result = compute_sum(1, 100)
    print(result)

if __name__ == "__main__":
    main()
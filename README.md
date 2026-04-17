# BF1 中文名 ID 哈希反查工具

## 最新文件

请使用 [`find_by_hash.py`](find_by_hash.py)，这是最新的哈希反查工具。

## 功能

给定前缀和目标哈希值，查找以该前缀开头、哈希值匹配目标的最短字符串。

## 使用方法

```python
from find_by_hash import find_string_by_hash

results = find_string_by_hash(prefix="daizhuentou", target_hash="7D543A64")
for s in results:
    print(s)
```

或直接运行：

```bash
python find_by_hash.py
```

## 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `prefix` | `str` | 字符串前缀 |
| `target_hash` | `str` | 目标哈希值（十六进制，如 `7D543A64`） |
| `max_suffix_len` | `int` | 最大后缀长度，默认 8 |

## 返回值

返回最短后缀长度下所有匹配的字符串列表。若未找到则返回空列表。

## 算法

采用中间相遇攻击（Meet-in-the-Middle）算法，将后缀拆为两半：

- 前半段：从 `prefix_hash` 正向计算所有可能的中间状态
- 后半段：从 `target` 逆向推算所需的中间状态
- 匹配两端状态即可还原完整后缀

将暴力搜索的复杂度从 O(62^n) 降至 O(62^(n/2))，后缀长度 8 以内可秒级完成。

## 字符集

后缀仅使用大小写英文字母、数字和连字符：`0-9 A-Z a-z -`

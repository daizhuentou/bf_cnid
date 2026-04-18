from itertools import product


def hash_string_id(string_id: str) -> int:
    result = 0xFFFFFFFF
    for char in string_id:
        result = ord(char) + 33 * result
    return result & 0xFFFFFFFF


def find_string_by_hash(prefix: str, target_hash: str, max_suffix_len: int = 8) -> list[str]:
    target = int(target_hash, 16)
    MOD = 0x100000000
    inv33 = pow(33, -1, MOD)

    prefix_hash = 0xFFFFFFFF
    for char in prefix:
        prefix_hash = ord(char) + 33 * prefix_hash
        prefix_hash &= 0xFFFFFFFF

    if prefix_hash == target:
        return [prefix]

    valid_chars = [ord(c) for c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-"]
    valid_set = set(valid_chars)

    needed = (target - 33 * prefix_hash) & 0xFFFFFFFF
    if needed in valid_set:
        return [prefix + chr(needed)]

    for suffix_len in range(2, max_suffix_len + 1):
        half1 = suffix_len // 2
        half2 = suffix_len - half1

        forward_dict = {}
        for combo in product(valid_chars, repeat=half1):
            state = prefix_hash
            for c in combo:
                state = c + 33 * state
                state &= 0xFFFFFFFF
            if state not in forward_dict:
                forward_dict[state] = combo

        results = []
        for combo in product(valid_chars, repeat=half2):
            state = target
            for c in reversed(combo):
                state = (state - c) * inv33 & 0xFFFFFFFF
            if state in forward_dict:
                first_half = forward_dict[state]
                results.append(prefix + "".join(chr(c) for c in first_half) + "".join(chr(c) for c in combo))

        if results:
            return results

    return []


if __name__ == "__main__":
    prefix = "daizhu"
    target_hash = "7D543A64"
    found_list = find_string_by_hash(prefix, target_hash)
    if found_list:
        for s in found_list:
            print(f"  {s}  哈希验证: {hex(hash_string_id(s))[2:].upper()}")
        print(f"最短后缀长度: {len(found_list[0]) - len(prefix)}")
        print(f"共找到 {len(found_list)} 个匹配:")
    else:
        print("未找到匹配")

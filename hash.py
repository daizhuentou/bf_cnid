import datetime

def hash_string_id(string_id):
    result = 0xFFFFFFFF
    for char in string_id:
        result = ord(char) + 33 * result
    return result & 0xFFFFFFFF


def find_target_hash_string(base_str, target_hash):
    characters = '-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'
    next_str = ''
    run_time = 0
    while True:
        current_str = base_str + next_str
        if len(current_str) > 30:
            return current_str + '长度超过三十位强制取消'
        if hash_string_id(current_str) == target_hash:
            return current_str
        elif hash_string_id(current_str) > target_hash:
            length = len(next_str)
            next_str_0 = ''
            for i in range(length):
                next_str_0 += '0'
            current_str = base_str + next_str_0
            if hash_string_id(current_str) < target_hash:
                next_str_0 = ''
                i_next = '0'
                for i in range(length - 1):
                    next_str_0 += '0'
                for i in str2int:
                    base_str_next = base_str + i + next_str_0
                    if run_time >= 10000:
                        return base_str_next+'卡死退出'
                    if hash_string_id(base_str_next) == target_hash:
                        return base_str_next
                    elif hash_string_id(base_str_next) > target_hash:
                        base_str = base_str + i_next
                        next_str = ''
                        if next_str_0 == '':
                            return base_str_next
                        break
                    else:
                        i_next = i
                        run_time += 1
            elif hash_string_id(current_str) > target_hash:
                next_str += 'z'
            else:
                return current_str
        else:
            next_str += 'z'


def slip_str():
    def replace_first_char(string, new_char):
        if not string:
            return string  # 如果字符串为空，直接返回
        return new_char + string[1:]

    # 示例
    original_string = "hello, world!"
    new_char = "H"
    modified_string = replace_first_char(original_string, new_char)
    print(modified_string)  # 输出: 'Hello, world!'


str2int = ['-','0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
           'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z','_', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
           'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']


def get_hash(base_str, target_hash):
    start_time = datetime.datetime.now()
    # 示例用法
    # base_str = "daizhu"
    target_hash = int(f'{target_hash}', 16)

    result = find_target_hash_string(base_str, target_hash)
    return result
    end_time = datetime.datetime.now()
    end_str = ''
    end_str += f'最接近的字符串: {result} \n'
    end_str += f'其哈希值: {hash_string_id(result)}\n'
    end_str += f'目标哈希值 {target_hash}\n'
    end_str += f'耗时 {end_time - start_time}'
    return end_str



if __name__ == '__main__':
    print(get_hash('daizhuentou', '7D543A64'))

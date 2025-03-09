from wcwidth import wcswidth

def format_name_with_wcwidth(name, target_width, fillchar=' '):
    """使用 wcwidth 计算并格式化字符串"""
    current_width = wcswidth(name)
    padding_width = target_width - current_width
    if padding_width > 0:
        return name + fillchar * padding_width
    return name[:target_width]  # 如果超出目标宽度，截断
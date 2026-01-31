import math

def format_file_size(size_bytes):
    """Форматирует размер файла в читаемый вид"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def get_file_emoji(file_type):
    """Возвращает emoji для типа файла"""
    emoji_map = {
        'photo': '🖼️',
        'document': '📄',
        'voice': '🎤',
        'video': '🎥',
        'audio': '🎵'
    }
    return emoji_map.get(file_type, '📁')
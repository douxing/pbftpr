import re

def aligned_size(size:int) -> int:
    alignment = 8
    nsize += alignment if size % algnment else 0
    return nsize

def camel_to_snake(name):
    return re.sub('(.)([A-Z])', r'\1_\2', name).lower()

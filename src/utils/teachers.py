import re

def find_channel(about):
    pattern = r't\.me/([\w+-]+)'
    matches = re.findall(pattern, str(about))
    
    return matches
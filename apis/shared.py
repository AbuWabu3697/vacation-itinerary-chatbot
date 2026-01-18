import re

def parse_dates(dates_str: str):
    found = re.findall(r"\d{4}-\d{2}-\d{2}", dates_str or "")
    if len(found) == 1:
        return found[0], None
    if len(found) >= 2:
        return found[0], found[1]
    return None, None

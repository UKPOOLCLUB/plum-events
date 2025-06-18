from django import template

register = template.Library()

@register.filter
def nested_score(value, key):
    if isinstance(value, dict):
        return value.get(str(key), "")
    return ""

@register.filter
def get_item(dictionary, key):
    if dictionary and key:
        return dictionary.get(str(key))
    return ""

@register.filter
def ordinal(value):
    try:
        value = int(value)
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(value)
        if medal:
            return f"{medal} {value}{ordinal_suffix(value)}"
        return f"{value}{ordinal_suffix(value)}"
    except (ValueError, TypeError):
        return value

def ordinal_suffix(value):
    if 10 <= value % 100 <= 20:
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')

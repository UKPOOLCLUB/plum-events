from django import template

register = template.Library()

@register.filter
def nested_score(value, key):
    if isinstance(value, dict):
        return value.get(str(key), "")
    return ""

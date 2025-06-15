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
        return dictionary.get(str(key))  # ensure key is str if it's coming from template
    return ""
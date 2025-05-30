from django import template

register = template.Library()

@register.filter
def get_match(matches_dict, key):
    return matches_dict.get(key)

@register.filter
def match_key(p1_id, p2_id):
    return f"{min(int(p1_id), int(p2_id))}-{max(int(p1_id), int(p2_id))}"

from django import template

register = template.Library()

@register.filter
def get_match(matches_dict, key):
    return matches_dict.get(key)

@register.filter
def match_key(p1_id, p2_id):
    return f"{min(int(p1_id), int(p2_id))}-{max(int(p1_id), int(p2_id))}"

@register.filter
def smart_int(value):
    """Show as int if whole number, else as float with 1 decimal place."""
    try:
        value = float(value)
        if value.is_integer():
            return str(int(value))
        return f"{value:.1f}"
    except (ValueError, TypeError):
        return value
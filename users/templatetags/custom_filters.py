from django import template

register = template.Library()

@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except IndexError:
        return ''

@register.filter
def dict_get(d, key):
    return d.get(key, 0)  # fallback to 0 if key not found

@register.simple_tag
def nested_dict_get(scores, player_id, hole):
    try:
        return scores.get(player_id, {}).get(hole, '')
    except:
        return ''

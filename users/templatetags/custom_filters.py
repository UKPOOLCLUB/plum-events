from django import template
from django.urls import reverse
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

@register.simple_tag
def game_link(code, event):
    if code == "mini_golf":
        return reverse("my_golf_score_entry", args=[event.code])
    elif code == "table_tennis":
        return reverse("table_tennis_game_view", args=[event.id])
    elif code == "pool_league":
        return reverse("pool_league_view", args=[event.id])
    elif code == "e_darts":
        return reverse("enter_edarts_results", args=[event.id])
    elif code == "killer_pool":
        return reverse("killer_game", args=[event.id])
    return "#"
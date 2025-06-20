from django import template
from events.models import EDartsResult

register = template.Library()

@register.filter
def darts_result(player, event):
    try:
        return EDartsResult.objects.get(event=event, participant=player)
    except EDartsResult.DoesNotExist:
        return None

@register.filter
def get_item(dictionary, key):
    return dictionary.get(f"group_{key}")
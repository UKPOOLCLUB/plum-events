from django import template

register = template.Library()

@register.filter
def get_winner_name(players):
    winner = players.filter(eliminated=False).first()
    return winner.participant.username if winner else "Unknown"


@register.filter
def ordinal(value):
    try:
        value = int(value)
        if 10 <= value % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
        return f"{value}{suffix}"
    except:
        return value

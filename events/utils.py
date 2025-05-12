import random
import math
from random import shuffle
from .models import MiniGolfGroup
from users.models import Participant

def generate_golf_groups(players, max_group_size=4, min_group_size=3):
    player_list = list(players)
    shuffle(player_list)
    total = len(player_list)

    # Calculate ideal group count
    group_count = math.ceil(total / max_group_size)

    # Distribute players as evenly as possible
    base_group_size = total // group_count
    remainder = total % group_count

    groups = []
    index = 0
    for i in range(group_count):
        size = base_group_size + (1 if i < remainder else 0)
        if size < min_group_size:
            raise ValueError("Cannot split players into valid groups")
        group = player_list[index:index+size]
        groups.append(group)
        index += size

    return groups

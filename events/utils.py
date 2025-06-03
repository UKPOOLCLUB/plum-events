import math
from random import shuffle

def create_balanced_groups(participants, max_group_size=5, min_group_size=3):
    """
    Splits a list of participants into balanced groups.
    Returns a list of lists of participants.
    """
    if not participants:
        return []

    participants = list(participants)
    shuffle(participants)
    total = len(participants)

    group_count = math.ceil(total / max_group_size)
    base_size = total // group_count
    remainder = total % group_count

    if base_size < min_group_size:
        raise ValueError("Cannot split players into valid groups")

    groups = []
    index = 0
    for i in range(group_count):
        size = base_size + (1 if i < remainder else 0)
        groups.append(participants[index:index + size])
        index += size

    return groups

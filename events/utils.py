# events/utils.py

from random import shuffle

def create_balanced_groups(players, max_group_size=5):
    """
    Randomly assigns players into groups of 3 to max_group_size (default 5).
    Ensures groups are balanced and avoids groups smaller than 3 unless unavoidable.
    """
    players = list(players)
    shuffle(players)

    num_players = len(players)
    groups = []

    i = 0
    while i < num_players:
        remaining = num_players - i

        # Choose the best group size based on what's left
        if remaining >= max_group_size:
            group_size = max_group_size
        elif remaining == 4:
            group_size = 4
        elif remaining == 3:
            group_size = 3
        elif remaining == 2 and groups:
            # Add remaining 2 to existing groups
            groups[-1].append(players[i])
            if i + 1 < num_players:
                groups[0].append(players[i + 1])
            break
        else:
            # Final fallback
            group_size = remaining

        groups.append(players[i:i + group_size])
        i += group_size

    return groups

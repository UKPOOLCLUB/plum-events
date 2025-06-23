from random import shuffle

def create_balanced_groups(players, max_group_size=5, min_group_size=3):
    """
    Splits players into balanced groups of 3–5, avoiding small groups (e.g. 1 or 2) at the end.
    Prioritizes balance over minimal number of groups.
    """
    players = list(players)
    shuffle(players)
    num_players = len(players)

    if num_players < min_group_size:
        return [players]

    # Try from 1 to N groups, prefer more balanced splits
    valid_groupings = []

    for num_groups in range(1, num_players + 1):
        base_size = num_players // num_groups
        remainder = num_players % num_groups

        # Distribute extra players across the first `remainder` groups
        group_sizes = [base_size + 1 if i < remainder else base_size for i in range(num_groups)]

        # Only accept groupings where all sizes are valid
        if all(min_group_size <= size <= max_group_size for size in group_sizes):
            valid_groupings.append(group_sizes)

    # Choose the most balanced valid grouping (smallest std deviation)
    def balance_score(sizes):
        return max(sizes) - min(sizes)

    best_sizes = min(valid_groupings, key=balance_score)

    # Assign players into groups
    groups = []
    index = 0
    for size in best_sizes:
        groups.append(players[index:index + size])
        index += size

    return groups

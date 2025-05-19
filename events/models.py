from django.db import models
from users.models import Participant
from django.contrib.postgres.fields import JSONField
import uuid

GAME_CHOICES = [
    ("pool_league", "Pool League"),
    ("pool_tournament", "Pool Tournament"),
    ("killer_pool", "Killer Pool"),
    ("six_red", "6 Red Shoot Out"),
    ("darts_golf", "Darts Golf"),
    ("darts_league", "Darts League"),
    ("round_the_clock", "Round the Clock"),
    ("mini_golf", "Mini-Golf"),
    ("table_tennis", "Table Tennis"),
    ("bowling", "Bowling"),
    ("axe_throwing", "Axe Throwing"),
    ("poker", "Poker"),
    ("snooker", "Snooker"),
]

class Event(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=8, unique=True)  # e.g. 4–8 letter join code
    date = models.DateField()
    selected_games = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    has_started = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code})"


class MiniGolfGroup(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='golf_groups')
    players = models.ManyToManyField(Participant, related_name='golf_groups')
    scorekeeper = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="scorekept_groups")
    created_at = models.DateTimeField(auto_now_add=True)

class MiniGolfScore(models.Model):
    group = models.ForeignKey(MiniGolfGroup, on_delete=models.CASCADE, related_name='scores')
    player = models.ForeignKey(Participant, on_delete=models.CASCADE)
    strokes = models.JSONField(default=dict)
    strokes_by_hole = models.JSONField(default=dict)  # store as {"1": 3, "2": 5, ...}
    points_awarded = models.IntegerField(default=0)

class MiniGolfScorecard(models.Model):
    group = models.OneToOneField('MiniGolfGroup', on_delete=models.CASCADE)
    data = models.JSONField(default=dict)  # e.g. { "player_id": { "1": 2, "2": 3, ... }, ... }
    last_updated = models.DateTimeField(auto_now=True)
    submitted = models.BooleanField(default=False)  # ✅ add this line

    def __str__(self):
        return f"Scorecard for Group {self.group.id} – Event {self.group.event.name}"

# New model in events/models.py
class MiniGolfConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='golf_config')
    holes = models.IntegerField(choices=[(9, "9 Holes"), (18, "18 Holes")], default=9)
    group_size_min = models.IntegerField(default=3)
    group_size_max = models.IntegerField(default=4)
    points_first = models.IntegerField(default=50)
    points_second = models.IntegerField(default=25)
    points_third = models.IntegerField(default=10)
    overall_bonus = models.IntegerField(default=25)

class PoolLeagueConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='pool_league_config')
    matches_per_pair = models.IntegerField(default=1)
    frames_per_match = models.IntegerField(default=3)
    points_per_frame = models.IntegerField(default=1)
    points_for_win = models.IntegerField(default=3)
    points_for_draw = models.IntegerField(default=1)
    points_for_loss = models.IntegerField(default=0)
    bonus_for_clean_sweep = models.IntegerField(default=0)

    def __str__(self):
        return f"Pool League Config for {self.event.name}"

class TableTennisConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='table_tennis_config')
    target_wins = models.PositiveIntegerField(default=7)  # e.g., first to 7 wins
    first_place_points = models.PositiveIntegerField(default=50)
    second_place_points = models.PositiveIntegerField(default=35)
    third_place_points = models.PositiveIntegerField(default=25)
    fourth_place_points = models.PositiveIntegerField(default=15)
    default_points = models.PositiveIntegerField(default=5)  # everyone else who finishes

    def get_points_for_rank(self, rank):
        if rank == 1:
            return self.first_place_points
        elif rank == 2:
            return self.second_place_points
        elif rank == 3:
            return self.third_place_points
        elif rank == 4:
            return self.fourth_place_points
        return self.default_points

    def __str__(self):
        return f"Table Tennis Config for {self.event.name}"

class TableTennisPlayer(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    games_won = models.PositiveIntegerField(default=0)
    has_finished = models.BooleanField(default=False)
    finish_rank = models.PositiveIntegerField(null=True, blank=True)  # 1st, 2nd, etc.
    points_awarded = models.PositiveIntegerField(default=0)
    queue_position = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['queue_position']

    def __str__(self):
        return f"{self.participant} (Wins: {self.games_won}, Queue: {self.queue_position})"


class KillerConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='killer_config')
    lives_per_player = models.IntegerField(default=3)
    points_per_survivor = models.IntegerField(default=50)
    bonus_black_pot = models.BooleanField(default=True)

    def __str__(self):
        return (f"Killer Config for {self.event.name}")

class DartsConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='darts_golf_config')
    points_first = models.IntegerField(default=50)
    points_second = models.IntegerField(default=25)
    points_third = models.IntegerField(default=10)

    def __str__(self):
        return f"Darts Config for {self.event.name}"

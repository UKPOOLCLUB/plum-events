from django.db import models
from users.models import Participant
from django.conf import settings
from django.contrib.postgres.fields import JSONField
import uuid

GAME_CHOICES = [
    ("pool_league", "Pool League"),
    ("pool_tournament", "Pool Tournament"),
    ("killer_pool", "Killer Pool"),
    ("six_red", "6 Red Shoot Out"),
    ("darts_golf", "Darts Golf"),
    ("e_darts", "E-Darts"),
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
    code = models.CharField(max_length=8, unique=True)
    date = models.DateField()
    selected_games = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    has_started = models.BooleanField(default=False)

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_events',
        null=True,  # ✅ temporarily allow null so we don’t break existing events
        blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.code})"


class MiniGolfGroup(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='golf_groups')
    players = models.ManyToManyField(Participant, related_name='golf_groups')
    scorekeeper = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, blank=True, related_name="scorekept_groups")
    group_number = models.PositiveIntegerField()  # ✅ ADD THIS LINE
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
    submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"Scorecard for Group {self.group.id} – Event {self.group.event.name}"

# New model in events/models.py
class MiniGolfConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='golf_config')
    holes = models.IntegerField(choices=[(18, "18 Holes"), (9, "9 Holes")], default=18)
    group_size_min = models.IntegerField(default=3)
    group_size_max = models.IntegerField(default=4)
    points_first = models.IntegerField(default=50)
    points_second = models.IntegerField(default=35)
    points_third = models.IntegerField(default=25)
    points_fourth = models.IntegerField(default=15)
    points_fifth = models.IntegerField(default=10)


class PoolLeagueConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='pool_league_config')
    matches_per_pair = models.IntegerField(default=1)
    frames_per_match = models.IntegerField(default=1)
    points_per_frame = models.IntegerField(default=1)
    points_first = models.IntegerField(default=50)
    points_second = models.IntegerField(default=35)
    points_third = models.IntegerField(default=25)
    points_fourth = models.IntegerField(default=15)
    points_fifth = models.IntegerField(default=10)
    points_sixth = models.IntegerField(default=5)
    points_for_win = models.IntegerField(default=3)
    points_for_draw = models.IntegerField(default=1)
    points_for_loss = models.IntegerField(default=0)

    def get_points_for_rank_range(self, start_rank, count):
        """Return average points across `count` ranks starting from `start_rank`."""
        total = 0
        for i in range(start_rank, start_rank + count):
            total += self.get_points_for_rank(i)
        return total / count if count > 0 else 0

    def get_points_for_rank(self, rank):
        if rank == 1:
            return self.points_first
        elif rank == 2:
            return self.points_second
        elif rank == 3:
            return self.points_third
        elif rank == 4:
            return self.points_fourth
        elif rank == 5:
            return self.points_fifth
        elif rank == 6:
            return self.points_sixth
        return 0  # No points for 7th or lower by default

    def __str__(self):
        return f"Pool League Config for {self.event.name}"

class PoolLeaguePlayer(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='pool_league_players')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    frames_won = models.PositiveIntegerField(default=0)  # optional, in case of tie-breaking
    points_awarded = models.PositiveIntegerField(default=0)
    finish_rank = models.PositiveIntegerField(null=True, blank=True)
    has_finished = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.participant}"

    @property
    def played(self):  # ✅ Optional
        return self.wins + self.losses

    class Meta:
        ordering = ['participant__username']

class PoolLeagueMatch(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='pool_league_matches')
    player1 = models.ForeignKey(PoolLeaguePlayer, on_delete=models.CASCADE, related_name='as_player1')
    player2 = models.ForeignKey(PoolLeaguePlayer, on_delete=models.CASCADE, related_name='as_player2')
    winner = models.ForeignKey(PoolLeaguePlayer, on_delete=models.SET_NULL, null=True, blank=True, related_name='wins_as_winner')
    score = models.CharField(max_length=20, blank=True)  # e.g. "1–0", "2–0", etc.
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player1} vs {self.player2}"


class TableTennisConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='table_tennis_config')
    target_wins = models.PositiveIntegerField(default=7)  # e.g., first to 7 wins
    points_first = models.IntegerField(default=50)
    points_second = models.IntegerField(default=35)
    points_third = models.IntegerField(default=25)
    points_fourth = models.IntegerField(default=15)
    points_fifth = models.IntegerField(default=10)
    points_sixth = models.IntegerField(default=5)

    def get_points_for_rank(self, rank):
        points_by_rank = [
            self.points_first,
            self.points_second,
            self.points_third,
            self.points_fourth,
            self.points_fifth,
            self.points_sixth,
        ]
        if 1 <= rank <= len(points_by_rank):
            return points_by_rank[rank - 1]
        return 0  # Default for ranks beyond 6

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
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='killer_config')
    points_first = models.IntegerField(default=50)
    points_second = models.IntegerField(default=35)
    points_third = models.IntegerField(default=25)
    points_fourth = models.IntegerField(default=15)
    points_fifth = models.IntegerField(default=10)
    points_sixth = models.IntegerField(default=5)

    def get_points_for_rank(self, rank):
        points_by_rank = [
            self.points_first,
            self.points_second,
            self.points_third,
            self.points_fourth,
            self.points_fifth,
            self.points_sixth,
        ]
        return points_by_rank[rank - 1] if 1 <= rank <= len(points_by_rank) else 0

    def __str__(self):
        return f"Killer Config for {self.event.name}"


class Killer(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    current_player_index = models.IntegerField(default=0)
    repeat_shot_pending = models.BooleanField(default=False)
    repeat_shot_forced = models.BooleanField(default=False)
    previous_player = models.ForeignKey(
        'KillerPlayer',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='was_previous'
    )
    is_complete = models.BooleanField(default=False)  # ✅ NEW FIELD

    def get_current_player(self):
        active = self.get_active_players()
        if self.repeat_shot_forced and self.previous_player:
            return self.previous_player
        if not active:
            return None
        return active[self.current_player_index % len(active)]

    def get_active_players(self):
        return list(self.killerplayer_set.filter(eliminated=False).order_by('turn_order'))

    def advance_turn(self):
        active_players = self.get_active_players()
        if not active_players:
            return
        self.current_player_index = (self.current_player_index + 1) % len(active_players)
        self.save()

    def move_back(self):
        active_players = self.get_active_players()
        if not active_players:
            return
        self.current_player_index = (self.current_player_index - 1) % len(active_players)
        self.save()

    def get_next_finish_position(self):
        total_players = self.killerplayer_set.count()
        eliminated_count = self.killerplayer_set.filter(eliminated=True).count()
        return total_players - eliminated_count

    def check_game_complete(self):
        active = self.killerplayer_set.filter(eliminated=False)
        if active.count() == 1:
            winner = active.first()
            self.is_complete = True
            self.save()

            # assign first place + points
            from .models import KillerConfig
            config = self.event.killer_config
            winner.finish_position = 1
            winner.points_awarded = config.get_points_for_rank(1)
            winner.save()

            p = winner.participant
            if not p.kept_scores:
                p.kept_scores = {}

            p.kept_scores["killer_pool"] = {
                "points": winner.points_awarded,
                "position": 1,
            }
            p.save()


class KillerPlayer(models.Model):
    killer_game = models.ForeignKey(Killer, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    lives = models.IntegerField(default=3)
    turn_order = models.IntegerField()
    eliminated = models.BooleanField(default=False)
    finish_position = models.PositiveIntegerField(null=True, blank=True)
    points_awarded = models.PositiveIntegerField(null=True, blank=True)

class EDartsConfig(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE, related_name='darts_config')
    points_first = models.IntegerField(default=50)
    points_second = models.IntegerField(default=35)
    points_third = models.IntegerField(default=25)
    points_fourth = models.IntegerField(default=15)
    points_fifth = models.IntegerField(default=10)

    def __str__(self):
        return f"Darts Config for {self.event.name}"

    def get_points_for_position(self, position):
        return {
            1: self.points_first,
            2: self.points_second,
            3: self.points_third,
            4: self.points_fourth,
            5: self.points_fifth
        }.get(position, 0)

class EDartsGroup(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='darts_groups')
    group_number = models.PositiveIntegerField()
    participants = models.ManyToManyField(Participant)
    scorekeeper = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, blank=True, related_name='darts_groups_led')
    submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"E-Darts Group {self.group_number} – {self.event.name}"


class EDartsResult(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='darts_results')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    finishing_position = models.PositiveIntegerField()
    points_awarded = models.PositiveIntegerField()

    class Meta:
        unique_together = ('event', 'participant')
        ordering = ['finishing_position']

    def __str__(self):
        return f"{self.participant.username} – Position {self.finishing_position} – {self.event.name}"


from django.contrib import admin
from .models import (
    Event,
    MiniGolfConfig,
    PoolLeagueConfig,
    PoolLeagueMatch,
    PoolLeaguePlayer,
    TableTennisConfig,
    KillerConfig,
    EDartsConfig,
    EDartsGroup,
    EDartsResult,
    MiniGolfScorecard,
    MiniGolfGroup,
    TableTennisPlayer,
)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "date", "has_started")
    list_filter = ("has_started", "date")
    search_fields = ("name", "code")

@admin.register(MiniGolfConfig)
class MiniGolfConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "holes", "group_size_min", "group_size_max", "points_first", "overall_bonus")
    search_fields = ("event__name",)

@admin.register(MiniGolfScorecard)
class MiniGolfScorecardAdmin(admin.ModelAdmin):
    list_display = ('group', 'last_updated', 'player_points')
    readonly_fields = ('last_updated',)

    def player_points(self, obj):
        scores = obj.group.scores.select_related('player')
        return ", ".join(f"{score.player.username} ({score.points_awarded})" for score in scores)

    player_points.short_description = "Players & Points"

@admin.register(MiniGolfGroup)
class MiniGolfGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'scorekeeper', 'created_at')
    list_filter = ('event',)
    search_fields = ('event__name', 'scorekeeper__username')
    filter_horizontal = ('players',)  # If players is a ManyToManyField

@admin.register(PoolLeagueConfig)
class PoolLeagueConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "matches_per_pair", "frames_per_match", "points_per_frame", "points_for_win")
    search_fields = ("event__name",)

@admin.register(PoolLeagueMatch)
class PoolLeagueMatchAdmin(admin.ModelAdmin):
    list_display = ('event', 'player1', 'player2', 'winner', 'completed')
    list_filter = ('event', 'completed')
    search_fields = ('player1__participant__username', 'player2__participant__username')
    ordering = ('event', 'completed', 'id')

@admin.register(PoolLeaguePlayer)
class PoolLeaguePlayerAdmin(admin.ModelAdmin):
    list_display = ('event', 'participant', 'wins', 'points_awarded', 'has_finished')
    list_filter = ('event',)
    search_fields = ('participant__username',)

@admin.register(TableTennisConfig)
class TableTennisConfigAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'target_wins',
        'first_place_points',
        'second_place_points',
        'third_place_points',
        'fourth_place_points',
        'default_points',
    )

@admin.register(TableTennisPlayer)
class TableTennisPlayerAdmin(admin.ModelAdmin):
    list_display = (
        'participant',
        'event',
        'games_won',
        'has_finished',
        'finish_rank',
        'points_awarded',
        'queue_position',
    )
    list_filter = ('event', 'has_finished')
    ordering = ('event', 'queue_position')

@admin.register(KillerConfig)
class KillerConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "lives_per_player", "points_per_survivor", "bonus_black_pot")
    search_fields = ("event__name",)


@admin.register(EDartsConfig)
class EDartsConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "points_first", "points_second", "points_third", "points_fourth", "points_fifth")
    search_fields = ("event__name",)

@admin.register(EDartsGroup)
class EDartsGroupAdmin(admin.ModelAdmin):
    list_display = ("event", "group_number")
    filter_horizontal = ("participants",)

@admin.register(EDartsResult)
class EDartsResultAdmin(admin.ModelAdmin):
    list_display = ("event", "participant", "finishing_position", "points_awarded")
    list_filter = ("event",)
    search_fields = ("participant__user__username", "event__name")

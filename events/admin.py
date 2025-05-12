from django.contrib import admin
from .models import (
    Event,
    MiniGolfConfig,
    PoolLeagueConfig,
    TableTennisConfig,
    KillerConfig,
    DartsConfig,
    MiniGolfScorecard
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
    list_display = ('group', 'last_updated')
    readonly_fields = ('last_updated',)

@admin.register(PoolLeagueConfig)
class PoolLeagueConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "matches_per_pair", "frames_per_match", "points_per_frame", "points_for_win")
    search_fields = ("event__name",)

@admin.register(TableTennisConfig)
class TableTennisConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "matches_to_stay_on", "points_per_win", "bonus_for_win_streak", "max_winstreak_bonus")
    search_fields = ("event__name",)

@admin.register(KillerConfig)
class KillerConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "lives_per_player", "points_per_survivor", "bonus_black_pot")
    search_fields = ("event__name",)

@admin.register(DartsConfig)
class DartsConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "points_first", "points_second", "points_third")
    search_fields = ("event__name",)

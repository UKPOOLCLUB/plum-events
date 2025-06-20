from django.contrib import admin
from .models import (
    Event,
    MiniGolfConfig,
    PoolLeagueConfig,
    PoolLeagueMatch,
    PoolLeaguePlayer,
    TableTennisConfig,
    KillerConfig,
    Killer,
    KillerPlayer,
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
    list_display = ("event", "holes", "group_size_min", "group_size_max", "points_first")
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
    list_display = ("event", "target_wins", "points_first", "points_second", "points_third", "points_fourth", "points_fifth",
                    "points_sixth")


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
    list_display = ("event", "points_first", "points_second", "points_third", "points_fourth", "points_fifth", "points_sixth")
    search_fields = ("event__name",)

@admin.register(KillerPlayer)
class KillerPlayerAdmin(admin.ModelAdmin):
    list_display = (
        'participant',
        'killer_game',
        'lives',
        'eliminated',
        'turn_order',
    )
    list_filter = ('killer_game__event', 'eliminated')
    ordering = ('killer_game__event', 'turn_order')
    search_fields = ('participant__username', 'killer_game__event__name')

@admin.register(Killer)
class KillerAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'current_player_index',
        'repeat_shot_pending',
        'repeat_shot_forced',
        'previous_player',
    )
    search_fields = ('event__name',)
    list_filter = ('event',)
    ordering = ('event__name',)


@admin.register(EDartsConfig)
class EDartsConfigAdmin(admin.ModelAdmin):
    list_display = ("event", "points_first", "points_second", "points_third", "points_fourth", "points_fifth")
    search_fields = ("event__name",)

@admin.register(EDartsGroup)
class EDartsGroupAdmin(admin.ModelAdmin):
    list_display = ('event', 'group_number', 'scorekeeper_display')
    list_filter = ('event',)
    search_fields = ('event__name', 'scorekeeper__username')
    filter_horizontal = ('participants',)

    def scorekeeper_display(self, obj):
        return obj.scorekeeper.username if obj.scorekeeper else "—"
    scorekeeper_display.short_description = 'Scorekeeper'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Optional: limit scorekeeper dropdown to participants of the group’s event
        if db_field.name == "scorekeeper" and request.resolver_match:
            try:
                object_id = request.resolver_match.kwargs.get('object_id')
                if object_id:
                    from .models import EDartsGroup
                    group = EDartsGroup.objects.get(pk=object_id)
                    kwargs["queryset"] = group.event.participant_set.all()
            except Exception:
                pass  # fallback to all participants

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(EDartsResult)
class EDartsResultAdmin(admin.ModelAdmin):
    list_display = ("event", "participant", "finishing_position", "points_awarded")
    list_filter = ("event",)
    search_fields = ("participant__username", "event__name")

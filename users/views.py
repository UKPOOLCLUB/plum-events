from django.shortcuts import render, redirect, get_object_or_404
from events.models import Event, GAME_CHOICES
from .models import Participant
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from collections import defaultdict
from pprint import pprint
from events.utils import generate_golf_groups
from events.models import MiniGolfConfig, MiniGolfGroup, KillerConfig, PoolLeagueConfig, PoolLeagueMatch, PoolLeaguePlayer, DartsConfig, TableTennisPlayer, TableTennisConfig
from django.db.models import Sum, Count
from random import shuffle


def enter_event_code(request):
    error = None

    if request.method == 'POST':
        code = request.POST.get('code')

        try:
            event = Event.objects.get(code__iexact=code)
            if event.has_started:
                error = "Code invalid — this tournament has already started."
            else:
                return redirect('enter_username', event_code=event.code)
        except Event.DoesNotExist:
            error = "Invalid code. Please try again."

    return render(request, 'users/enter_event_code.html', {'error': error})


def enter_username(request, event_code):
    event = get_object_or_404(Event, code__iexact=event_code)
    error = None

    if request.method == 'POST':
        username = request.POST.get('username')

        if not username:
            error = "Please enter a username."
        elif Participant.objects.filter(username=username, event=event).exists():
            error = "That username is already taken for this event."
        else:
            participant = Participant.objects.create(username=username, event=event)
            request.session['participant_id'] = str(participant.id)
            return redirect('waiting_room', event_code=event.code)

    return render(request, 'users/enter_username.html', {'event': event, 'error': error})


def waiting_room(request, event_code):
    event = get_object_or_404(Event, code__iexact=event_code)

    # 🔁 Redirect players if the event has started
    if event.has_started:
        return redirect('live_leaderboard', event_code=event.code)

    participants = event.participants.all().order_by('joined_at')

    participant_id = request.session.get('participant_id')
    is_host = False

    if participant_id:
        try:
            participant = Participant.objects.get(id=participant_id, event=event)
        except Participant.DoesNotExist:
            pass

    return render(request, 'users/waiting_room.html', {
        'event': event,
        'participants': participants
    })


@user_passes_test(lambda u: u.is_superuser)
def host_dashboard(request):
    from events.models import Event
    events = Event.objects.all().order_by('-date')

    return render(request, 'users/host_dashboard.html', {
        'events': events
    })

@user_passes_test(lambda u: u.is_superuser)
def start_event(request, event_code):
    event = get_object_or_404(Event, code__iexact=event_code)

    if request.method == 'POST':
        event.has_started = True
        event.save()

        # ✅ Mini Golf Setup
        if "mini_golf" in event.selected_games:
            MiniGolfConfig.objects.get_or_create(event=event, defaults={"holes": 9})
            groups = generate_golf_groups(event)
            for group_players in groups:
                group = MiniGolfGroup.objects.create(
                    event=event,
                    scorekeeper=group_players[0]
                )
                group.players.set(group_players)
                group.save()

        # ✅ Pool League Setup
        if "pool_league" in event.selected_games:
            PoolLeagueConfig.objects.get_or_create(event=event, defaults={
                'matches_per_pair': 1,
                'frames_per_match': 1,
                'points_per_frame': 1,
                'points_first': 50,
                'points_second': 35,
                'points_third': 25,
                'points_fourth': 15,
                'points_fifth': 10,
                'points_sixth': 5,
                'points_for_win': 1,
                'points_for_draw': 0,
                'points_for_loss': 0,
            })

            participants = list(event.participants.all())
            players = []
            for participant in participants:
                player = PoolLeaguePlayer.objects.create(event=event, participant=participant)
                players.append(player)

            # Generate round-robin matches
            from itertools import combinations
            for p1, p2 in combinations(players, 2):
                PoolLeagueMatch.objects.create(
                    event=event,
                    player1=p1,
                    player2=p2,
                    completed=False
                )

        # ✅ Table Tennis Setup
        if "table_tennis" in event.selected_games:
            # Create default config if not already set
            TableTennisConfig.objects.get_or_create(event=event, defaults={
                'target_wins': 7,
                'first_place_points': 50,
                'second_place_points': 35,
                'third_place_points': 25,
                'fourth_place_points': 15,
                'default_points': 5,
            })

            participants = list(event.participants.all())
            shuffle(participants)

            for idx, participant in enumerate(participants):
                TableTennisPlayer.objects.create(
                    event=event,
                    participant=participant,
                    queue_position=idx
                )

        return redirect('host_dashboard')

    return redirect('host_dashboard')

def leaderboard(request, event_code):
    event = get_object_or_404(Event, code__iexact=event_code)
    participants = event.participants.all()

    print("\n=== EVENT SELECTED GAMES ===")
    pprint(event.selected_games)

    # Map game codes to readable names
    game_dict = dict(GAME_CHOICES)
    selected_game_names = [game_dict.get(code, code) for code in event.selected_games]

    print("\n=== GAME NAME MAPPING ===")
    for code in event.selected_games:
        print(f"{code} → {game_dict.get(code, code)}")

    # Gather scores using username as key
    results = defaultdict(lambda: {name: 0 for name in selected_game_names})
    participant_map = {}

    for participant in participants:
        username = participant.username
        participant_map[username] = participant

        print(f"\n--- Participant: {username} ---")
        for code in event.selected_games:
            name = game_dict.get(code, code)
            if code == "table_tennis":
                try:
                    tt_player = TableTennisPlayer.objects.get(event=event, participant=participant)
                    points = tt_player.points_awarded
                except TableTennisPlayer.DoesNotExist:
                    points = 0
                print(f"{code} ({name}) → [TableTennisPlayer] {points}")
                results[username][name] = points
            else:
                game_data = participant.kept_scores.get(code, {})
                print(f"{code} ({name}) → {game_data}")

                if isinstance(game_data, dict):
                    results[username][name] = game_data.get("points", 0)
                elif isinstance(game_data, int):
                    results[username][name] = game_data
                else:
                    results[username][name] = 0

    print("\n=== RESULTS TABLE ===")
    pprint(dict(results))

    # Build leaderboard
    leaderboard_data = []

    for username, score_row in results.items():
        total_points = sum(score_row.values())
        event_wins = 0

        for game in selected_game_names:
            top_score = max(user_scores[game] for user_scores in results.values())
            if score_row[game] == top_score and top_score > 0:
                event_wins += 1

        leaderboard_data.append({
            "username": username,
            "scores": score_row,
            "total": total_points,
            "wins": event_wins,
        })

    leaderboard_data.sort(key=lambda x: (-x["total"], -x["wins"], x["username"].lower()))

    print("\n=== FINAL LEADERBOARD ===")
    pprint(leaderboard_data)

    return render(request, "users/leaderboard.html", {
        "event": event,
        "leaderboard": leaderboard_data,
        "event_names": selected_game_names,
        "active_game": selected_game_names[0] if selected_game_names else None,
        "selected_games": event.selected_games,
        "selected_game_names": selected_game_names,
    })
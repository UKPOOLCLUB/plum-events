from django.shortcuts import render, redirect, get_object_or_404
from events.models import Event, GAME_CHOICES
from .models import Participant
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from collections import defaultdict
from events.utils import generate_golf_groups
from events.models import MiniGolfConfig, MiniGolfGroup, KillerConfig, PoolLeagueConfig, DartsConfig, TableTennisConfig
from django.db.models import Sum, Count


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

        if "mini_golf" in event.selected_games:
            # ✅ Create config if needed
            MiniGolfConfig.objects.get_or_create(event=event, defaults={"holes": 9})

            # ✅ Generate groups
            groups = generate_golf_groups(event)  # <-- this returns a list of lists

            for group_players in groups:
                group = MiniGolfGroup.objects.create(
                    event=event,
                    scorekeeper=group_players[0]  # ✅ First player is scorekeeper
                )
                group.players.set(group_players)
                group.save()

        return redirect('host_dashboard')

    return redirect('host_dashboard')


def leaderboard(request, event_code):
    event = get_object_or_404(Event, code__iexact=event_code)
    participants = event.participants.all()

    # Placeholder results: simulate each participant having event scores
    # Replace this with DB-driven logic later
    event_names = ["Mini-Golf", "E-Darts", "Ping Pong", "Pool", "Killer"]
    fake_results = defaultdict(lambda: {name: 0 for name in event_names})
    game_dict = dict(GAME_CHOICES)
    selected_game_names = [game_dict.get(code, code) for code in event.selected_games]

    # TEMP: assign fake scores
    for i, participant in enumerate(participants):
        for j, event_name in enumerate(event_names):
            fake_results[participant][event_name] = (i + j) % 5  # just some dummy data

    leaderboard_data = []

    for participant in participants:
        scores = fake_results[participant]
        total = sum(scores.values())
        event_wins = 0
        for event_name in event_names:
            max_score = max([p_scores[event_name] for p_scores in fake_results.values()])
            if scores[event_name] == max_score:
                event_wins += 1

        leaderboard_data.append({
            'username': participant.username,
            'scores': scores,
            'total': total,
            'wins': event_wins,
        })

    # Sort: total desc, wins desc, name asc
    leaderboard_data.sort(key=lambda x: (-x['total'], -x['wins'], x['username'].lower()))

    active_game = 'Mini-Golf'  # ← Hardcoded for now

    return render(request, 'users/leaderboard.html', {
        'event': event,
        'leaderboard': leaderboard_data,
        'event_names': event_names,
        'active_game': active_game,
        'selected_games': event.selected_games,
        'selected_game_names': selected_game_names,

    })
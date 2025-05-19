from django.forms import modelformset_factory
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from .models import MiniGolfGroup, MiniGolfScore, MiniGolfScorecard, MiniGolfConfig, TableTennisConfig, TableTennisPlayer
from django.contrib import messages
from django.http import HttpResponseForbidden
from events.models import Event, Participant

def enter_golf_scores(request, group_id):
    group = get_object_or_404(MiniGolfGroup, id=group_id)
    event = group.event
    holes = event.golf_config.holes
    players = group.players.all()

    # 🧠 Get saved scores from MiniGolfScorecard
    scorecard = MiniGolfScorecard.objects.filter(group=group).first()
    scores = scorecard.data if scorecard else {}

    participant_id = request.session.get('participant_id')
    can_edit = False

    if participant_id:
        try:
            participant = Participant.objects.get(id=participant_id, event=event)
            if participant == group.scorekeeper:
                can_edit = True
                if scorecard and scorecard.submitted:
                    can_edit = False
        except Participant.DoesNotExist:
            pass

    # Recalculate totals from scores
    totals = {}
    for player in players:
        player_scores = scores.get(player.username, {})
        totals[player.id] = sum(int(v) for v in player_scores.values())

    return render(request, 'events/enter_golf_scores.html', {
        'group': group,
        'players': players,
        'holes': list(range(1, holes + 1)),  # So it's indexable
        'can_edit': can_edit,
        'scorekeeper': group.scorekeeper,
        'totals': totals,
        'event': event,
        'scores': scores
    })

@csrf_exempt
def save_golf_score(request):
    if request.method == "POST":
        try:
            group_id = int(request.POST.get("group_id"))
            username = request.POST.get("username")
            hole = str(request.POST.get("hole"))
            strokes = int(request.POST.get("strokes"))

            group = MiniGolfGroup.objects.get(id=group_id)
            event = group.event

            player = Participant.objects.get(username=username, event=event)

            scorecard, _ = MiniGolfScorecard.objects.get_or_create(group=group)

            if username not in scorecard.data:
                scorecard.data[username] = {}

            scorecard.data[username][hole] = strokes
            scorecard.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


def redirect_to_golf_group(request, event_code):
    event = get_object_or_404(Event, code__iexact=event_code)
    participant_id = request.session.get('participant_id')

    if not participant_id:
        messages.error(request, "You must join the event first.")
        return redirect('enter_event_code')

    participant = get_object_or_404(Participant, id=participant_id, event=event)

    try:
        group = participant.golf_groups.get(event=event)
        return redirect('enter_golf_scores', group_id=group.id)
    except MiniGolfGroup.DoesNotExist:
        return HttpResponseForbidden("You are not assigned to a golf group.")



def submit_golf_scorecard(request, group_id):
    group = get_object_or_404(MiniGolfGroup, id=group_id)
    scorecard = MiniGolfScorecard.objects.get(group=group)
    config = MiniGolfConfig.objects.get(event=group.event)
    holes = config.holes

    print("Hello Submit_score")

    # Validate complete scorecards
    for username, hole_scores in scorecard.data.items():
        if len(hole_scores) < holes:
            return JsonResponse({"success": False, "error": f"{username} has not completed all holes."})

    # Calculate totals
    player_totals = []
    for username, hole_scores in scorecard.data.items():
        total = sum(int(v) for v in hole_scores.values())
        player_totals.append((username, total))

    # Sort by strokes (ascending = better)
    player_totals.sort(key=lambda x: x[1])

    # Assign points
    for i, (username, strokes) in enumerate(player_totals):
        participant = Participant.objects.get(username=username, event=group.event)

        # Assign position-based points
        if i == 0:
            points = config.points_first
        elif i == 1:
            points = config.points_second
        elif i == 2:
            points = config.points_third
        else:
            points = 0

        if not participant.kept_scores:
            participant.kept_scores = {}

        # ✅ Store both points and finishing position
        participant.kept_scores["mini_golf"] = {
            "points": points,
            "position": i + 1,
            "strokes": strokes,
        }
        participant.save()

    scorecard.submitted = True
    scorecard.save()

    return redirect('live_leaderboard', event_code=group.event.code)


def table_tennis_game_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    players = TableTennisPlayer.objects.filter(event=event).order_by('queue_position')
    config = event.table_tennis_config
    all_players = TableTennisPlayer.objects.filter(event=event).order_by('-games_won', 'queue_position')

    context = {
        'event': event,
        'players': players,  # ordered queue (playing, next, waiting)
        'all_players': all_players,  # for leaderboard
        'config': config,
    }
    return render(request, 'events/table_tennis_game.html', context)


def submit_table_tennis_result(request, event_id, winner_id):
    event = get_object_or_404(Event, id=event_id)
    config = event.table_tennis_config
    players = list(TableTennisPlayer.objects.filter(event=event, has_finished=False).order_by('queue_position'))

    if len(players) < 2:
        return redirect('table_tennis_game_view', event_id=event.id)

    p1, p2 = players[0], players[1]
    winner = p1 if p1.id == winner_id else p2
    loser = p2 if winner == p1 else p1

    # Update winner's games won
    winner.games_won += 1
    winner.save()

    # Check if winner has completed the target
    if winner.games_won >= config.target_wins:
        winner.has_finished = True
        finishers = TableTennisPlayer.objects.filter(event=event, has_finished=True).count()
        winner.finish_rank = finishers + 1
        winner.points_awarded = config.get_points_for_rank(winner.finish_rank)
        winner.save()

    # Build new queue
    queue = players.copy()
    queue.remove(winner)
    queue.remove(loser)

    if not loser.has_finished:
        queue.append(loser)

    if not winner.has_finished:
        queue.append(winner)

    # Reassign queue positions
    for i, player in enumerate(queue):
        player.queue_position = i
        player.save()

    return redirect('table_tennis_game_view', event_id=event.id)

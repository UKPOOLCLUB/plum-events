from django.forms import modelformset_factory
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import MiniGolfGroup, MiniGolfScore, MiniGolfScorecard
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
            can_edit = (participant == group.scorekeeper)
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
        'holes': range(1, holes + 1),
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



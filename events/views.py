from django.forms import modelformset_factory
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from .models import MiniGolfGroup, MiniGolfScore, MiniGolfScorecard, MiniGolfConfig, TableTennisConfig, TableTennisPlayer
from .models import PoolLeaguePlayer, PoolLeagueMatch, EDartsGroup, EDartsConfig, EDartsResult
from .models import Killer, KillerPlayer
from .utils import create_balanced_groups
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from events.models import Event, Participant
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q


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

def generate_golf_groups(event):
    # Get all participants
    players = Participant.objects.filter(event=event)

    # Clear any existing groups for this event
    MiniGolfGroup.objects.filter(event=event).delete()

    # Create balanced groups
    grouped_players = create_balanced_groups(players)

    # Save each group to DB
    for i, group_players in enumerate(grouped_players, start=1):
        group = MiniGolfGroup.objects.create(event=event, group_number=i)
        group.players.set(group_players)

    return MiniGolfGroup.objects.filter(event=event)

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

    # Safely get scorecard or handle error
    try:
        scorecard = MiniGolfScorecard.objects.get(group=group)
    except MiniGolfScorecard.DoesNotExist:
        return HttpResponseBadRequest("Scorecard not found. Please save scores before submitting.")

    config = MiniGolfConfig.objects.get(event=group.event)
    holes = config.holes

    # Validate complete scorecards
    for username, hole_scores in scorecard.data.items():
        if len(hole_scores) < holes:
            return JsonResponse({"success": False, "error": f"{username} has not completed all holes."})

    # Calculate totals
    player_totals = []
    for username, hole_scores in scorecard.data.items():
        total = sum(int(v) for v in hole_scores.values())
        player_totals.append((username, total))

    player_totals.sort(key=lambda x: x[1])  # sort by strokes

    for i, (username, strokes) in enumerate(player_totals):
        participant = Participant.objects.get(username=username, event=group.event)

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

        participant.kept_scores["mini_golf"] = {
            "points": points,
            "position": i + 1,
            "strokes": strokes,
        }
        participant.save()

    scorecard.submitted = True
    scorecard.save()

    return redirect('live_leaderboard', event_code=group.event.code)

def golf_scorecard_state(request, group_id):
    scorecard = get_object_or_404(MiniGolfScorecard, group_id=group_id)
    return JsonResponse({
        'submitted': scorecard.submitted,
        'last_updated': scorecard.updated_at.isoformat()
    })

def table_tennis_game_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    config = event.table_tennis_config

    # Only active players in the queue (exclude those who finished)
    players = TableTennisPlayer.objects.filter(
        event=event,
        has_finished=False
    ).order_by('queue_position')

    # All players, including finished ones, for leaderboard
    finished = TableTennisPlayer.objects.filter(
        event=event,
        has_finished=True
    ).order_by('finish_rank')

    active = TableTennisPlayer.objects.filter(
        event=event,
        has_finished=False
    ).order_by('queue_position')

    all_players = list(finished) + list(active)

    context = {
        'event': event,
        'players': players,  # used for current match-up and "up next"
        'all_players': all_players,  # used for full leaderboard
        'config': config,
    }
    return render(request, 'events/table_tennis_game.html', context)



def submit_table_tennis_result(request, event_id, winner_id):
    event = get_object_or_404(Event, id=event_id)
    config = event.table_tennis_config
    players = list(TableTennisPlayer.objects.filter(event=event, has_finished=False).order_by('queue_position'))

    if len(players) < 2:
        return redirect('table_tennis_game_view', event_id=event.id)

    # Identify the two players
    p1, p2 = players[0], players[1]
    winner = p1 if p1.id == winner_id else p2
    loser = p2 if winner == p1 else p1

    # Update winner's score
    winner.games_won += 1
    winner.save()

    # If winner hits target, mark as finished
    if winner.games_won >= config.target_wins:
        winner.has_finished = True
        finishers = TableTennisPlayer.objects.filter(event=event, has_finished=True).count()
        winner.finish_rank = finishers + 1
        winner.points_awarded = config.get_points_for_rank(winner.finish_rank)
        winner.save()

    # Remove both players from the queue
    players.remove(winner)
    players.remove(loser)

    # Rebuild queue:
    new_queue = []

    # 1. If winner is NOT finished, they go first
    if not winner.has_finished:
        new_queue.append(winner)

    # 2. If there are any remaining players, they follow
    for p in players:
        new_queue.append(p)

    # 3. Loser goes to the back if not finished
    if not loser.has_finished:
        new_queue.append(loser)

    # Reassign queue positions
    for i, player in enumerate(new_queue):
        player.queue_position = i
        player.save()

    return redirect('table_tennis_game_view', event_id=event.id)

def table_tennis_state(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    players = TableTennisPlayer.objects.filter(event=event).order_by('finishing_position', 'order')

    return JsonResponse({
        'player_order': [p.participant.username for p in players],
        'finished_count': players.filter(finishing_position__isnull=False).count()
    })


from django.http import HttpResponse

def pool_league_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participant_id = request.session.get('participant_id')

    if not participant_id:
        return redirect('live_leaderboard', event_code=event.code)

    try:
        current_player = PoolLeaguePlayer.objects.select_related('participant').get(
            event=event,
            participant_id=participant_id
        )
    except PoolLeaguePlayer.DoesNotExist:
        return redirect('enter_username', event_code=event.code)

    # Fetch only this player's matches
    matches = PoolLeagueMatch.objects.filter(
        event=event
    ).filter(
        Q(player1=current_player) | Q(player2=current_player)
    ).select_related('player1__participant', 'player2__participant')

    # Annotate opponent for each match so templates are simple
    for match in matches:
        match.opponent = match.player2 if match.player1 == current_player else match.player1

    all_players = PoolLeaguePlayer.objects.filter(event=event).select_related('participant')
    league_completed = is_pool_league_complete(event)

    standings = []
    if league_completed:
        standings = all_players.order_by('finish_rank')

    context = {
        'event': event,
        'current_player': current_player,
        'matches': matches,
        'all_players': all_players,
        'league_completed': league_completed,
        'standings': standings,
    }
    return render(request, "events/pool_league_view.html", context)


@require_POST
def submit_pool_match_result(request):
    match_id = request.POST.get('match_id')
    winner_id = request.POST.get('winner_id')
    participant_id = request.session.get('participant_id')

    if not participant_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})

    try:
        match = PoolLeagueMatch.objects.get(id=match_id)
        submitting_player = PoolLeaguePlayer.objects.get(event=match.event, participant_id=participant_id)
        winner = PoolLeaguePlayer.objects.get(id=winner_id)
    except PoolLeagueMatch.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Match not found'})
    except PoolLeaguePlayer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid player'})

    if submitting_player != match.player1 and submitting_player != match.player2:
        return JsonResponse({'success': False, 'error': 'Not authorized to submit this result'})

    match.winner = winner
    match.completed = True
    match.save()

    winner.wins += 1
    winner.save()

    if is_pool_league_complete(match.event):
        finalize_pool_league(match.event)

    return JsonResponse({'success': True})


def is_pool_league_complete(event):
    return not PoolLeagueMatch.objects.filter(event=event, completed=False).exists()


def finalize_pool_league(event):
    if not is_pool_league_complete(event):
        return False

    players = list(PoolLeaguePlayer.objects.filter(event=event))

    if all(p.has_finished for p in players):
        return False

    config = event.pool_league_config

    # Group players by number of wins
    wins_groups = defaultdict(list)
    for p in players:
        wins_groups[p.wins].append(p)

    sorted_win_totals = sorted(wins_groups.keys(), reverse=True)

    current_rank = 1
    ranked_players = []

    for wins in sorted_win_totals:
        group = wins_groups[wins]

        if len(group) == 1:
            ranked_players.append((group[0], current_rank))
            current_rank += 1
        elif len(group) == 2:
            # Head-to-head logic
            p1, p2 = group
            match = PoolLeagueMatch.objects.filter(
                event=event,
                player1__in=[p1, p2],
                player2__in=[p1, p2],
                completed=True
            ).first()

            if match and match.winner:
                winner = match.winner
                loser = p1 if winner == p2 else p2
                ranked_players.append((winner, current_rank))
                ranked_players.append((loser, current_rank + 1))
                current_rank += 2
            else:
                # No valid match found — fallback to shared points
                avg_points = config.get_points_for_rank(current_rank, 2)
                for player in group:
                    ranked_players.append((player, current_rank, avg_points))
                current_rank += 2

        else:
            # 3+ way tie: split points
            avg_points = config.get_points_for_rank_range(current_rank, len(group))
            for player in group:
                ranked_players.append((player, current_rank, avg_points))
            current_rank += len(group)

    # Assign points and ranks
    for item in ranked_players:
        if len(item) == 2:
            player, rank = item
            points = config.get_points_for_rank(rank)
        else:
            player, rank, points = item

        player.finish_rank = rank
        player.points_awarded = int(Decimal(points).to_integral_value(rounding=ROUND_HALF_UP))
        player.has_finished = True
        player.save()

    return True

def pool_league_state(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    players = PoolLeaguePlayer.objects.filter(event=event).select_related('participant')

    league_state = sorted(
        [(p.participant.username, p.points_awarded or 0) for p in players],
        key=lambda x: (-x[1], x[0].lower())
    )

    return JsonResponse({
        "league_state": league_state
    })

def generate_darts_groups(event):

    players = Participant.objects.filter(event=event)
    EDartsGroup.objects.filter(event=event).delete()

    groups = create_balanced_groups(players)

    for i, group_players in enumerate(groups, start=1):
        group = EDartsGroup.objects.create(event=event, group_number=i)
        group.participants.set(group_players)

    return EDartsGroup.objects.filter(event=event)


def enter_edarts_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    groups = EDartsGroup.objects.filter(event=event)
    config = event.darts_config
    participant_id = request.session.get('participant_id')

    if not participant_id:
        messages.error(request, "You must join the event first.")
        return redirect('enter_event_code')

    participant = get_object_or_404(Participant, id=participant_id, event=event)

    if event.edarts_completed:
        return render(request, 'events/enter_edarts_results.html', {
            'event': event,
            'groups': groups,
            'readonly': True,
        })

    if request.method == 'POST':
        # 🧠 Existing validation code here...
        for group in groups:
            positions = []
            for player in group.participants.all():
                key = f"position_{group.id}_{player.id}"
                val = request.POST.get(key)
                if not val:
                    messages.error(request, f"Missing finishing position for {player.username} in Group {group.group_number}")
                    return redirect('enter_edarts_results', event_id=event.id)
                positions.append(int(val))

            if len(set(positions)) != len(positions):
                messages.error(request, f"Duplicate positions in Group {group.group_number}.")
                return redirect('enter_edarts_results', event_id=event.id)

            if sorted(positions) != list(range(1, len(positions) + 1)):
                messages.error(request, f"Invalid positions in Group {group.group_number}. Use 1 to {len(positions)}.")
                return redirect('enter_edarts_results', event_id=event.id)

        # ✅ Save results
        for group in groups:
            for player in group.participants.all():
                key = f"position_{group.id}_{player.id}"
                position = int(request.POST.get(key))
                points = config.get_points_for_position(position)

                EDartsResult.objects.update_or_create(
                    event=event,
                    participant=player,
                    defaults={
                        'finishing_position': position,
                        'points_awarded': points
                    }
                )

                if not player.kept_scores:
                    player.kept_scores = {}

                player.kept_scores["e_darts"] = {
                    "points": points,
                    "position": position
                }
                player.save()

        # 🔒 Mark event as completed
        event.edarts_completed = True
        event.save()

        return redirect('live_leaderboard', event_code=event.code)

    return render(request, 'events/enter_edarts_results.html', {
        'event': event,
        'groups': groups
    })

def killer_game_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    killer = get_object_or_404(Killer, event=event)
    players = KillerPlayer.objects.filter(killer_game=killer).order_by('turn_order')

    current_player = killer.get_current_player()

    # ✅ Get next player (skipping eliminated)
    next_player = None
    if current_player:
        current_index = list(players).index(current_player)
        for offset in range(1, len(players)):
            candidate = players[(current_index + offset) % len(players)]
            if not candidate.eliminated:
                next_player = candidate
                break

    context = {
        'event': event,
        'killer': killer,
        'players': players,
        'current_player': current_player,
        'next_player': next_player,
        'previous_player': killer.previous_player,
        'repeat_shot_pending': killer.repeat_shot_pending,
        'repeat_shot_forced': killer.repeat_shot_forced,
    }
    return render(request, 'events/killer_game.html', context)

@require_POST
def killer_submit_turn(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    killer = get_object_or_404(Killer, event=event)
    players = KillerPlayer.objects.filter(killer_game=killer).order_by('turn_order')
    current_player = killer.get_current_player()

    action = request.POST.get('action')

    if action == 'successful_pot':
        killer.previous_player = current_player
        killer.repeat_shot_pending = False
        killer.repeat_shot_forced = False
        killer.advance_turn()

    elif action == 'lose_one_life':
        current_player.lives -= 1
        if current_player.lives <= 0:
            current_player.eliminated = True
            current_player.save()
            handle_killer_elimination(killer, current_player)
            killer.check_game_complete()
        else:
            current_player.save()

        killer.previous_player = current_player
        killer.advance_turn()


    elif action == 'lose_two_lives':
        current_player.lives -= 2
        if current_player.lives <= 0:
            current_player.eliminated = True
            current_player.save()
            handle_killer_elimination(killer, current_player)
            killer.check_game_complete()
        else:
            current_player.save()

        killer.previous_player = current_player
        killer.advance_turn()

    elif action == 'add_life':
        current_player.lives += 1
        current_player.save()
        killer.previous_player = current_player
        killer.advance_turn()

    elif action == 'repeat_previous':
        killer.repeat_shot_pending = True
        killer.repeat_shot_forced = True
        killer.current_player_index = (killer.current_player_index - 1) % players.count()

    killer.save()
    return redirect('killer_game', event_id=event.id)

def handle_killer_elimination(killer, player):
    total_players = KillerPlayer.objects.filter(killer_game=killer).count()
    eliminated_count = KillerPlayer.objects.filter(killer_game=killer, eliminated=True).count()

    # Position is from the bottom up (e.g. 8th place = first eliminated in 8-player game)
    finish_position = total_players - eliminated_count + 1

    player.finish_position = finish_position
    player.points_awarded = killer.event.killer_config.get_points_for_rank(finish_position)
    player.save()

    # Update participant's kept_scores
    participant = player.participant
    if not participant.kept_scores:
        participant.kept_scores = {}

    participant.kept_scores["killer_pool"] = {
        "points": player.points_awarded,
        "position": finish_position,
    }
    participant.save()

    # Check if only one player remains
    alive_players = KillerPlayer.objects.filter(killer_game=killer, eliminated=False)
    if alive_players.count() == 1:
        killer.is_complete = True
        killer.save()

        winner = alive_players.first()
        winner.finish_position = 1
        winner.points_awarded = killer.event.killer_config.get_points_for_rank(1)
        winner.save()

        wp = winner.participant
        if not wp.kept_scores:
            wp.kept_scores = {}

        wp.kept_scores["killer_pool"] = {
            "points": winner.points_awarded,
            "position": 1,
        }
        wp.save()

def killer_game_state(request, event_id):
    killer = get_object_or_404(Killer, event_id=event_id)
    current_player = killer.get_current_player()
    is_complete = killer.is_complete
    winner = killer.get_winner()

    return JsonResponse({
        'current_player': current_player.participant.username if current_player else None,
        'is_complete': is_complete,
        'winner': winner.participant.username if winner else None,
    })

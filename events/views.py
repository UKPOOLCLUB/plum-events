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
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse, HttpResponseServerError
from events.models import Event, Participant
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q
from uuid import UUID
from django.template.loader import render_to_string
import hashlib
import json


import logging
logger = logging.getLogger(__name__)

def enter_golf_scores(request, group_id):
    group = get_object_or_404(MiniGolfGroup, id=group_id)
    event = group.event
    holes = event.golf_config.holes
    players = group.players.all()

    # Ensure scorecard exists
    scorecard, _ = MiniGolfScorecard.objects.get_or_create(group=group)
    scores = scorecard.data if scorecard and scorecard.data else {}

    participant_id = request.session.get('participant_id')
    can_edit = False

    if participant_id:
        try:
            participant = Participant.objects.get(id=participant_id, event=event)
            if participant == group.scorekeeper and not scorecard.submitted:
                can_edit = True
        except Participant.DoesNotExist:
            pass

    player_metadata = []

    for player in players:
        try:
            player_scores = scores.get(str(player.id), {})
            total = sum(int(v) for v in player_scores.values())
        except Exception:
            total = 0

        result = {
            'id': player.id,
            'username': player.username,
            'is_scorekeeper': player == group.scorekeeper,
            'total': total,
        }

        if scorecard.submitted:
            kept = player.kept_scores.get("mini_golf", {})
            result["position"] = kept.get("position")
            result["points"] = kept.get("points")

        player_metadata.append(result)

    # ✅ Now sort once, after the loop
    if scorecard.submitted:
        player_metadata.sort(key=lambda x: (x.get("position") or 999, x["username"]))
    else:
        player_metadata.sort(key=lambda x: x["username"])

    return render(request, 'events/enter_golf_scores.html', {
        'group': group,
        'players': player_metadata,  # ✅ updated list
        'holes': list(range(1, holes + 1)),
        'can_edit': can_edit,
        'scorekeeper': group.scorekeeper,
        'totals': {},  # unused now, could be removed entirely
        'event': event,
        'scores': scores,
        'scorecard': scorecard,
    })


@csrf_exempt
def save_golf_score(request):
    print("SGS triggered")
    if request.method == "POST":
        try:
            group_id = int(request.POST.get("group_id"))
            # player_id is a UUID string
            player_id = request.POST.get("player_id")
            hole = str(request.POST.get("hole"))
            strokes = int(request.POST.get("strokes"))

            group = MiniGolfGroup.objects.get(id=group_id)
            event = group.event
            player = Participant.objects.get(id=player_id, event=event)
            username = player.username

            scorecard, _ = MiniGolfScorecard.objects.get_or_create(group=group)

            if not scorecard.data:
                scorecard.data = {}

            if username not in scorecard.data:
                scorecard.data[username] = {}

            scorecard.data[username][hole] = strokes
            scorecard.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})

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
        elif i == 3:
            points = config.points_fourth
        elif i == 4:
            points = config.points_fifth
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
        'last_updated': scorecard.last_updated.isoformat()
    })

def table_tennis_game_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    config = event.table_tennis_config

    # Active players (not finished)
    players = TableTennisPlayer.objects.filter(
        event=event,
        has_finished=False
    ).order_by('queue_position')

    # All players (used for leaderboard)
    finished = TableTennisPlayer.objects.filter(
        event=event,
        has_finished=True
    ).order_by('finish_rank')

    all_players = list(finished) + list(players)

    # Determine if the game is complete (e.g., 6 players have finished)
    game_complete = finished.count() >= 6

    context = {
        'event': event,
        'players': players,
        'all_players': all_players,
        'config': config,
        'game_complete': game_complete,
    }
    return render(request, 'events/table_tennis_game.html', context)

def submit_table_tennis_result(request, event_id, winner_id):
    event = get_object_or_404(Event, id=event_id)
    config = event.table_tennis_config
    players = list(TableTennisPlayer.objects.filter(event=event, has_finished=False).order_by('queue_position'))

    # End game if all point-awarding ranks have been assigned
    finishers_count = TableTennisPlayer.objects.filter(event=event, has_finished=True).count()
    max_rank = 6  # Matches your config: points awarded down to 6th place
    if finishers_count >= max_rank:
        return redirect('table_tennis_game_view', event_id=event.id)

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

    # ✅ If only one player remains and all others are finished, finish them
    remaining = TableTennisPlayer.objects.filter(event=event, has_finished=False)
    if remaining.count() == 1:
        last_player = remaining.first()
        finishers_count = TableTennisPlayer.objects.filter(event=event, has_finished=True).count()
        last_player.has_finished = True
        last_player.finish_rank = finishers_count + 1
        last_player.points_awarded = config.get_points_for_rank(last_player.finish_rank)
        last_player.save()

    return redirect('table_tennis_game_view', event_id=event.id)

import traceback

def table_tennis_state(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)
        config = event.table_tennis_config
        players = list(TableTennisPlayer.objects.filter(event=event).order_by('has_finished', 'queue_position'))

        # Count how many players have finished
        finished_count = sum(p.has_finished for p in players)

        # Dynamically count how many point-places are awarded
        points_fields = [
            config.points_first,
            config.points_second,
            config.points_third,
            config.points_fourth,
            config.points_fifth,
            config.points_sixth,
        ]
        places_awarded = sum(1 for points in points_fields if points > 0)

        game_complete = finished_count >= places_awarded

        data = []
        for p in players:
            data.append({
                'id': p.id,
                'username': p.participant.username,
                'games_won': p.games_won,
                'has_finished': p.has_finished,
                'finish_rank': p.finish_rank,
                'points_awarded': p.points_awarded,
                'is_playing': not p.has_finished and players.index(p) < 2,
                'is_next': not p.has_finished and players.index(p) == 2,
            })

        return JsonResponse({
            'game_complete': game_complete,
            'players': data,
        })

    except Exception as e:
        return HttpResponseServerError("Error: " + str(e))

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

    all_players = get_player_standings(event)
    league_completed = is_pool_league_complete(event)

    standings = []
    if league_completed:
        standings = sorted(
            all_players,
            key=lambda p: p.finish_rank if p.finish_rank else 9999
        )
    else:
        standings = all_players

    context = {
        'event': event,
        'current_player': current_player,
        'matches': matches,
        'all_players': all_players,
        'league_completed': league_completed,
        'standings': standings,
    }
    return render(request, "events/pool_league_view.html", context)

def get_player_standings(event):
    players = PoolLeaguePlayer.objects.filter(event=event).select_related("participant")
    matches = PoolLeagueMatch.objects.filter(event=event, completed=True)

    stats = defaultdict(lambda: {"wins": 0, "losses": 0, "player": None})

    for player in players:
        stats[player.id]["player"] = player

    for match in matches:
        if match.winner:
            winner_id = match.winner.id
            loser_id = match.player1.id if match.player2.id == winner_id else match.player2.id
            stats[winner_id]["wins"] += 1
            stats[loser_id]["losses"] += 1

    # Attach calculated stats to each player object
    annotated_players = []
    for data in stats.values():
        p = data["player"]
        p.calculated_wins = data["wins"]
        p.calculated_losses = data["losses"]
        p.calculated_played = data["wins"] + data["losses"]
        annotated_players.append(p)

    # Sort by wins descending, then name
    return sorted(annotated_players, key=lambda x: (-x.calculated_wins, x.participant.username.lower()))

@require_POST
def submit_pool_match_result(request):
    match_id = request.POST.get('match_id')
    result = request.POST.get('result')
    raw_participant_id = request.POST.get('player_id') or request.session.get('participant_id')

    if not (match_id and result and raw_participant_id):
        return HttpResponseBadRequest("Missing required fields.")

    try:
        participant_id = UUID(raw_participant_id)
        match = PoolLeagueMatch.objects.get(id=int(match_id))
        submitting_player = PoolLeaguePlayer.objects.get(event=match.event, participant__id=participant_id)
    except (ValueError, PoolLeagueMatch.DoesNotExist, PoolLeaguePlayer.DoesNotExist):
        return HttpResponseBadRequest("Invalid match or player.")

    if match.completed:
        return HttpResponseBadRequest("Match already completed.")

    if submitting_player not in [match.player1, match.player2]:
        return HttpResponseForbidden("You are not part of this match.")

    opponent = match.player2 if submitting_player == match.player1 else match.player1

    if result == "win":
        match.winner = submitting_player
    elif result == "loss":
        match.winner = opponent
    else:
        return HttpResponseBadRequest("Invalid result.")

    match.completed = True
    match.save()
    submitting_player.save()
    opponent.save()

    if is_pool_league_complete(match.event):
        finalize_pool_league(match.event)

    # Prepare data for updated UI
    players = get_player_standings(match.event)

    matches = PoolLeagueMatch.objects.filter(
        event=match.event
    ).filter(
        Q(player1=submitting_player) | Q(player2=submitting_player)
    )

    for m in matches:
        m.opponent = m.player2 if m.player1 == submitting_player else m.player1

    html = render_to_string("events/partials/pool_league_update.html", {
        "matches": matches,
        "all_players": players,
        "current_player": submitting_player,
        "event": match.event,
        "league_completed": not PoolLeagueMatch.objects.filter(event=match.event, completed=False).exists(),
    })

    return HttpResponse(html)


def is_pool_league_complete(event):
    return not PoolLeagueMatch.objects.filter(event=event, completed=False).exists()

def finalize_pool_league(event):
    if not is_pool_league_complete(event):
        return False

    players = get_player_standings(event)

    if all(p.has_finished for p in players):
        return False

    config = event.pool_league_config

    # Group players by live win counts
    wins_groups = defaultdict(list)
    for p in players:
        wins_groups[p.calculated_wins].append(p)

    sorted_win_totals = sorted(wins_groups.keys(), reverse=True)

    current_rank = 1
    ranked_players = []

    for wins in sorted_win_totals:
        group = wins_groups[wins]

        if len(group) == 1:
            ranked_players.append((group[0], current_rank))
            current_rank += 1

        elif len(group) == 2:
            # Head-to-head tiebreaker
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
                # No result or unclear – split average points
                avg_points = config.get_points_for_rank(current_rank, 2)
                for player in group:
                    ranked_players.append((player, current_rank, avg_points))
                current_rank += 2

        else:
            # 3+ way tie – average the points
            avg_points = config.get_points_for_rank_range(current_rank, len(group))
            for player in group:
                ranked_players.append((player, current_rank, avg_points))
            current_rank += len(group)

    # Assign final rank and points
    for item in ranked_players:
        if len(item) == 2:
            player, rank = item
            points = config.get_points_for_rank(rank)
        else:
            player, rank, points = item

        player.finish_rank = rank
        player.points_awarded = int(Decimal(points).to_integral_value(rounding=ROUND_HALF_UP))
        player.has_finished = True

        # Optional: Store for reference
        player.wins = getattr(player, "calculated_wins", 0)
        player.losses = getattr(player, "calculated_losses", 0)

        player.save()

    return True

def recalculate_league_standings(event):
    players = PoolLeaguePlayer.objects.filter(event=event)
    matches = PoolLeagueMatch.objects.filter(event=event, completed=True)

    # Reset
    players.update(wins=0, losses=0)

    for match in matches:
        if match.winner:
            match.winner.wins += 1
            loser = match.player1 if match.player2 == match.winner else match.player2
            loser.losses += 1

    for player in players:
        player.save()


def pool_league_state(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    players = PoolLeaguePlayer.objects.filter(event=event).select_related('participant')

    league_state = sorted(
        [(p.participant.username, p.points_awarded or 0) for p in players],
        key=lambda x: (-x[1], x[0].lower())
    )

    # Generate hash to detect change
    hash_input = json.dumps(league_state, sort_keys=True).encode()
    state_hash = hashlib.md5(hash_input).hexdigest()

    return JsonResponse({
        "state_hash": state_hash,
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

    # ✅ Readonly if all groups are submitted
    readonly = all(group.submitted for group in groups)
    is_host = event.host == participant.username

    # ✅ Scorers per group
    scorers = {
        f"group_{group.id}": (group.scorekeeper == participant or is_host)
        for group in groups
    }

    return render(request, 'events/enter_edarts_results.html', {
        'event': event,
        'groups': groups,
        'readonly': readonly,
        'scorers': scorers,
        'participant': participant,
        'is_host': is_host,

    })


@require_POST
def submit_edarts_group(request, event_id, group_id):
    event = get_object_or_404(Event, id=event_id)
    group = get_object_or_404(EDartsGroup, id=group_id, event=event)
    config = event.darts_config
    participant_id = request.session.get('participant_id')
    participant = get_object_or_404(Participant, id=participant_id, event=event)

    # Only allow scorer or host to submit
    if group.scorekeeper != participant:
        messages.error(request, "You are not allowed to submit results for this group.")
        return redirect('enter_edarts_results', event_id=event.id)

    positions = []
    for player in group.participants.all():
        key = f"position_{player.id}"
        val = request.POST.get(key)
        if not val:
            messages.error(request, f"Missing position for {player.username} in Group {group.group_number}")
            return redirect('enter_edarts_results', event_id=event.id)
        positions.append(int(val))

    if len(set(positions)) != len(positions):
        messages.error(request, f"Duplicate positions in Group {group.group_number}")
        return redirect('enter_edarts_results', event_id=event.id)

    if sorted(positions) != list(range(1, len(positions) + 1)):
        messages.error(request, f"Positions must be 1 to {len(positions)}")
        return redirect('enter_edarts_results', event_id=event.id)

    # Save results
    for player in group.participants.all():
        position = int(request.POST.get(f"position_{player.id}"))
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
        group.submitted = True
        group.save()

    messages.success(request, f"Group {group.group_number} results submitted.")
    return redirect('enter_edarts_results', event_id=event.id)

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

    if request.user != event.host and not request.user.is_superuser:
        return HttpResponseForbidden("Only the host can update the Killer game.")

    killer = get_object_or_404(Killer, event=event_id)
    current_player = killer.get_current_player()
    action = request.POST.get('action')

    advance_turn = True  # Only advance if not eliminated

    if action == "successful_pot":
        pass  # Just advance
    elif action == "lose_one_life":
        current_player.lives -= 1
        current_player.save()
        if current_player.lives <= 0 and not current_player.eliminated:
            current_player.eliminated = True
            handle_killer_elimination(killer, current_player)
            advance_turn = False
    elif action == "lose_two_lives":
        current_player.lives -= 2
        current_player.save()
        if current_player.lives <= 0 and not current_player.eliminated:
            current_player.eliminated = True
            handle_killer_elimination(killer, current_player)
            advance_turn = False
    elif action == "add_life":
        current_player.lives += 1
        current_player.save()
    elif action == "move_back":
        killer.move_back()
        advance_turn = False
    elif action == "move_forward":
        killer.advance_turn()
        advance_turn = False

    if advance_turn:
        killer.advance_turn()

    killer.save()
    return redirect('killer_game', event_id=event.id)

def handle_killer_elimination(killer, player):
    alive_players = KillerPlayer.objects.filter(killer_game=killer, eliminated=False).count()
    finish_position = alive_players

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
    event = get_object_or_404(Event, id=event_id)
    killer = get_object_or_404(Killer, event=event)
    players = KillerPlayer.objects.filter(killer_game=killer).order_by('turn_order')

    return JsonResponse({
        'is_complete': killer.is_complete,
        'current_player': killer.get_current_player().participant.username,
        'players': [
            {
                'username': p.participant.username,
                'lives': p.lives,
                'eliminated': p.eliminated,
                'is_current': p == killer.get_current_player(),
                'finish_position': p.finish_position,
                'points_awarded': p.points_awarded,
            }
            for p in players
        ]
    })

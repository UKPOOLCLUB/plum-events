from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse
from events.models import Event, GAME_CHOICES
from .models import Participant, EventAvailability, Booking
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from collections import defaultdict
from django.views.decorators.http import require_POST
from pprint import pprint
from events.utils import create_balanced_groups
from events.models import MiniGolfConfig, MiniGolfGroup, MiniGolfScorecard, EDartsConfig, EDartsGroup, TableTennisPlayer, TableTennisConfig
from events.models import Killer, KillerPlayer, KillerConfig
from events.models import PoolLeagueConfig, PoolLeagueMatch, PoolLeaguePlayer
from .forms import BookingContactForm, ContactForm
from .models import Booking, ContactEnquiry
from .forms import BookingContactForm
from django.db.models import Sum, Count
from datetime import date, timedelta, time, datetime
from random import shuffle
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

def landing_page(request):
    form = ContactForm()
    return render(request, 'users/landing.html', {"form": form})


EVENT_PRICING = {
    'Pool League and Killer': 15,
    'Mini Golf': 20,
    'E-darts Tournament': 15,
    'Darts League': 10,
    'Bowling': 20,
    'Poker': 10,
    'Shuffle Board': 15,
    'Table Tennis': 10,
    'Snooker': 15,
    'Boule': 10,
}

EVENT_CHOICES = [
    {"name": "Pool League and Killer", "icon": "fa-circle-dot text-warning"},
    {"name": "Mini Golf", "icon": "fa-golf-ball-tee text-success"},
    {"name": "E-darts Tournament", "icon": "fa-bullseye text-danger"},
    {"name": "Darts League", "icon": "fa-bullseye text-info"},
    {"name": "Bowling", "icon": "fa-bowling-ball text-primary"},
    {"name": "Poker", "icon": "fa-club text-warning"},
    {"name": "Shuffle Board", "icon": "fa-table-tennis-paddle-ball text-secondary"},
    {"name": "Table Tennis", "icon": "fa-table-tennis-paddle-ball text-danger"},
    {"name": "Snooker", "icon": "fa-circle text-info"},
    {"name": "Boule", "icon": "fa-bowling-ball text-success"},
]

def get_quote(request):
    total = None
    group_size = None
    selected_events = []
    show_continue = False

    if request.method == 'POST':
        group_size = int(request.POST.get('group_size', 0))
        selected_events = request.POST.getlist('events')
        total = request.POST.get('total')
        confirm = request.POST.get('confirm_quote')

        # If the user clicked "Continue to calendar", save and redirect
        if confirm == "1":
            print("DEBUG: Saving to session - group_size:", group_size)
            print("DEBUG: Saving to session - selected_events:", selected_events)
            print("DEBUG: Saving to session - quote_total:", total)
            request.session['group_size'] = group_size
            request.session['selected_events'] = selected_events
            request.session['quote_total'] = total
            return redirect('calendar_page')

        # Else: Just show the quote, do not redirect yet
        event_total = sum(EVENT_PRICING[event] for event in selected_events if event in EVENT_PRICING)
        total = event_total * group_size + 50  # admin fee
        show_continue = True

    context = {
        'group_size': group_size,
        'selected_events': selected_events,
        'total': total,
        'event_pricing': EVENT_PRICING,
        'events_with_icons': EVENT_CHOICES,
        'show_continue': show_continue,
    }
    return render(request, 'users/get_quote.html', context)

def get_expected_duration(num_events):
    if num_events == 3:
        return "4 – 5 hours"
    elif num_events == 4:
        return "5 – 6 hours"
    elif num_events == 5:
        return "7–8 hours"
    elif num_events == 6:
        return "8–9 hours"
    return "N/A"

def view_calendar(request):
    return render(request, 'users/calendar.html')

def calendar_page(request):
    group_size = request.session.get('group_size')
    selected_events = request.session.get('selected_events')
    quote_total = request.session.get('quote_total')
    num_events = len(selected_events)
    expected_duration = get_expected_duration(num_events)

    if not group_size or not selected_events:
        return redirect('get_quote')

    if request.method == 'POST':
        selected_date_str = request.POST.get('event_date')
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        num_events = len(selected_events)

        # Check if start_time is posted (user clicked Continue)
        if 'start_time' in request.POST:
            # Save choices to session for use in summary
            request.session['event_date'] = selected_date_str
            request.session['start_time'] = request.POST.get('start_time')
            return redirect('booking_summary')  # <<< THIS DOES THE REDIRECT

        # Otherwise, just show times for chosen date
        available_times = get_available_start_times(selected_date, num_events)
        context = {
            'selected_date': selected_date_str,
            'available_times': available_times,
            'group_size': group_size,
            'selected_events': selected_events,
            'quote_total': quote_total,
            "expected_duration": expected_duration,
        }
        return render(request, 'users/calendar.html', context)

    context = {
        'group_size': group_size,
        'selected_events': selected_events,
        'quote_total': quote_total,
        "expected_duration": expected_duration,
    }
    return render(request, 'users/calendar.html', context)


# Example calendar_data view
def calendar_data(request):
    # Only fetch dates with status "available"
    available_qs = EventAvailability.objects.filter(status='available')
    available_dates = [d.date.strftime('%Y-%m-%d') for d in available_qs]
    print('DEBUG: available_dates:', available_dates)  # Add this for terminal debug!
    return JsonResponse({
        "available": available_dates,
    })


def get_available_start_times(selected_date, num_events):
    day = selected_date.weekday()
    start_hour = 10 if day < 5 else 11  # Weekday = 10am, Weekend = 11am
    total_duration = timedelta(minutes=90 * num_events)

    latest_end_time = time(20, 0)
    latest_start_dt = datetime.combine(selected_date, latest_end_time) - total_duration

    available_times = []
    current_dt = datetime.combine(selected_date, time(start_hour, 0))

    while current_dt <= latest_start_dt:
        available_times.append(current_dt.strftime("%H:%M"))
        current_dt += timedelta(minutes=30)

    return available_times

# users/views.py

def confirm_booking(request):
    if request.method == 'POST':
        group_size = request.session.get('group_size')
        selected_events = request.session.get('selected_events')
        quote_total = request.session.get('quote_total')
        event_date = request.POST.get('event_date')
        start_time = request.POST.get('start_time')
        # Optionally, validate all these fields

        # Create the booking
        booking = Booking.objects.create(
            group_size=group_size,
            selected_events=selected_events,
            quote_total=quote_total,
            event_date=event_date,
            start_time=start_time
        )
        # Clear session if you want to reset for next booking

        return render(request, 'users/booking_confirmed.html', {'booking': booking})

    # If GET or missing data, redirect to calendar
    return redirect('calendar_page')


def booking_summary(request):
    group_size = request.session.get('group_size')
    selected_events = request.session.get('selected_events')
    num_events = len(selected_events)
    expected_duration = get_expected_duration(num_events)
    quote_total = request.session.get('quote_total')
    event_date = request.session.get('event_date')
    if isinstance(event_date, str):
        event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
    start_time = request.session.get('start_time')

    if not all([group_size, selected_events, quote_total, event_date, start_time]):
        return redirect('calendar_page')

    # Find or create a booking object in session
    booking_id = request.session.get('booking_id')
    booking = Booking.objects.filter(id=booking_id).first() if booking_id else None

    if request.method == 'POST':
        form = BookingContactForm(request.POST)
        if form.is_valid():
            if not booking:
                booking = Booking.objects.create(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data['phone'],
                    event_date=event_date,
                    start_time=start_time,
                    group_size=group_size,
                    selected_events=selected_events,
                    quote_total=quote_total,
                )
                request.session['booking_id'] = booking.id
            else:
                booking.name = form.cleaned_data['name']
                booking.email = form.cleaned_data['email']
                booking.phone = form.cleaned_data['phone']
                booking.save()
            # 🚩 This is the important line:
            return JsonResponse({'success': True, 'booking_id': booking.id})
        else:
            return JsonResponse({'error': 'Please fill in all fields.'})


    else:
        form = BookingContactForm(initial={
            'name': booking.name if booking else "",
            'email': booking.email if booking else "",
            'phone': booking.phone if booking else "",
        })

    context = {
        'booking': {
            'id': booking.id if booking else None,
            'group_size': group_size,
            'selected_events': selected_events,
            'quote_total': quote_total,
            'event_date': event_date,
            'start_time': start_time,
            'expected_duration': expected_duration,
        },
        'form': form,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'users/booking_summary.html', context)


def pay_now(request):
    # Only allow POST for now (optional: GET could show an error or redirect)
    if request.method != "POST":
        messages.error(request, "Invalid access to payment page.")
        return redirect('booking_summary')

    # Fetch booking details from session
    group_size = request.session.get('group_size')
    selected_events = request.session.get('selected_events')
    quote_total = request.session.get('quote_total')
    event_date = request.session.get('event_date')
    if isinstance(event_date, str):
        event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
    start_time = request.session.get('start_time')

    if not all([group_size, selected_events, quote_total, event_date, start_time]):
        messages.error(request, "Missing booking details.")
        return redirect('booking_summary')

    # Here you would process the payment (call Stripe/PayPal etc)
    # For now, we’ll just simulate success
    # Optionally, you could create a Booking model instance here and save details to DB

    # Clear session booking data if desired
    # request.session.pop('group_size', None)
    # request.session.pop('selected_events', None)
    # request.session.pop('quote_total', None)
    # request.session.pop('event_date', None)
    # request.session.pop('start_time', None)

    # Render a confirmation page
    return render(request, 'users/payment_success.html', {
        'group_size': group_size,
        'selected_events': selected_events,
        'quote_total': quote_total,
        'event_date': event_date,
        'start_time': start_time,
    })

def send_booking_confirmation_email(booking):
    subject = "Your Plum Events Booking Confirmation"
    message = (
        f"Hi {booking.name},\n\n"
        f"Thank you for booking with Plum Events!\n"
        f"Your event is confirmed for {booking.event_date} at {booking.start_time}.\n"
        f"Group size: {booking.group_size}\n"
        f"Events: {', '.join(booking.selected_events)}\n"
        f"Total Paid: £{booking.quote_total}\n\n"
        f"We look forward to seeing you!\n\n"
        f"Plum Events Team"
    )
    recipients = [booking.email, "bookings@plumevents.com"]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)


def contact_us(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Get the fields from your form
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            subject = f"Contact form submission from {name}"
            body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

            send_mail(
                subject,
                body,
                'contact@plumevents.co.uk',    # FROM address (shows as the sender)
                ['contact@plumevents.co.uk'],  # TO address (your mailbox)
                fail_silently=False,
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return redirect('landing_page')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ContactForm()
    return render(request, "users/landing.html", {"form": form})



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
        username = request.POST.get('username', '').strip()

        if not username:
            error = "Please enter a username."
        elif ' ' in username or len(username) > 12:
            error = "Username must be max 12 characters with no spaces."
        elif Participant.objects.filter(username__iexact=username, event=event).exists():
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

def event_state(request, event_code):
    event = get_object_or_404(Event, code__iexact=event_code)

    # If the event has started, signal redirect
    if event.has_started:
        return JsonResponse({'started': True})

    # Otherwise return current participant list
    participants = event.participants.all().order_by('joined_at')
    participant_data = [{'username': p.username} for p in participants]

    return JsonResponse({
        'started': False,
        'participants': participant_data
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
        event.host = request.user  # ✅ Set host here
        event.save()

        participants = list(event.participants.all())

        # ✅ Shared Group Generation (for golf/darts)
        group_list = []
        if "mini_golf" in event.selected_games or "e_darts" in event.selected_games:
            group_list = create_balanced_groups(participants)

        # ✅ Mini Golf Setup
        if "mini_golf" in event.selected_games:
            MiniGolfConfig.objects.get_or_create(event=event, defaults={"holes": 18})
            MiniGolfGroup.objects.filter(event=event).delete()

            for i, group_players in enumerate(group_list, start=1):
                group = MiniGolfGroup.objects.create(
                    event=event,
                    group_number=i,
                    scorekeeper=group_players[0]
                )
                group.players.set(group_players)

        # ✅ E-Darts Setup
        if "e_darts" in event.selected_games:
            EDartsConfig.objects.get_or_create(event=event, defaults={
                "points_first": 50,
                "points_second": 35,
                "points_third": 25,
                "points_fourth": 15,
                "points_fifth": 10,
            })
            EDartsGroup.objects.filter(event=event).delete()

            for i, group_players in enumerate(group_list, start=1):
                group = EDartsGroup.objects.create(
                    event=event,
                    group_number=i,
                    scorekeeper=group_players[0]  # 🧠 assign first player as scorekeeper
                )
                group.participants.set(group_players)

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

            players = [
                PoolLeaguePlayer.objects.create(event=event, participant=p)
                for p in participants
            ]

            from itertools import combinations
            for p1, p2 in combinations(players, 2):
                PoolLeagueMatch.objects.create(
                    event=event,
                    player1=p1,
                    player2=p2,
                    completed=False
                )

        # ✅ Killer Setup
        if "killer_pool" in event.selected_games:
            KillerConfig.objects.get_or_create(event=event, defaults={
                'points_first': 50,
                'points_second': 35,
                'points_third': 25,
                'points_fourth': 15,
                'points_fifth': 10,
                'points_sixth': 5,
            })

            Killer.objects.filter(event=event).delete()
            killer = Killer.objects.create(event=event)

            shuffle(participants)
            for idx, participant in enumerate(participants):
                KillerPlayer.objects.create(
                    killer_game=killer,
                    participant=participant,
                    turn_order=idx,
                    lives=getattr(event, 'killer_starting_lives', 3)
                )

        # ✅ Table Tennis Setup
        if "table_tennis" in event.selected_games:
            TableTennisConfig.objects.get_or_create(event=event, defaults={
                'target_wins': 7,
                'points_first': 50,
                'points_second': 35,
                'points_third': 25,
                'points_fourth': 15,
                'points_fifth': 10,
                'points_sixth': 5,
            })

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

            elif code == "pool_league":
                try:
                    pl_player = PoolLeaguePlayer.objects.get(event=event, participant=participant)
                    points = pl_player.points_awarded
                except PoolLeaguePlayer.DoesNotExist:
                    points = 0
                print(f"{code} ({name}) → [PoolLeaguePlayer] {points}")
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

def leaderboard_state(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participants = event.participants.all()
    game_dict = dict(GAME_CHOICES)
    selected_game_names = [game_dict.get(code, code) for code in event.selected_games]

    results = defaultdict(lambda: {name: 0 for name in selected_game_names})

    for participant in participants:
        username = participant.username
        for code in event.selected_games:
            name = game_dict.get(code, code)
            if code == "table_tennis":
                try:
                    points = TableTennisPlayer.objects.get(event=event, participant=participant).points_awarded
                except TableTennisPlayer.DoesNotExist:
                    points = 0
                results[username][name] = points

            elif code == "pool_league":
                try:
                    points = PoolLeaguePlayer.objects.get(event=event, participant=participant).points_awarded
                except PoolLeaguePlayer.DoesNotExist:
                    points = 0
                results[username][name] = points

            else:
                game_data = participant.kept_scores.get(code, {})
                if isinstance(game_data, dict):
                    results[username][name] = game_data.get("points", 0)
                elif isinstance(game_data, int):
                    results[username][name] = game_data
                else:
                    results[username][name] = 0

    leaderboard_state = sorted(
        [(username, sum(scores.values())) for username, scores in results.items()],
        key=lambda x: (-x[1], x[0].lower())
    )

    return JsonResponse({
        "leaderboard_state": leaderboard_state
    })


@require_POST
@csrf_exempt
def create_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    amount = int(float(booking.quote_total) * 100)

    # This string is required by Stripe!
    success_url = "https://plum-events.onrender.com/payment/success/?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse('payment_cancel'))

    print("DEBUG Stripe success_url:", success_url)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': f'Plum Events Booking #{booking.id}',
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            customer_email=getattr(booking, 'email', None),
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'booking_id': str(booking.id),
            }
        )
        return JsonResponse({'id': session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def booking_confirm(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        # Use instance=booking only if BookingContactForm is a ModelForm
        form = BookingContactForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('booking_confirm', booking_id=booking.id)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Invalid form data.'})
    else:
        form = BookingContactForm(instance=booking)
    context = {
        'booking': booking,
        'form': form,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,  # <-- UPDATED
    }
    return render(request, 'users/booking_summary.html', context)  # Use your actual template filename


def payment_success(request):
    session_id = request.GET.get('session_id')
    booking = None

    # Log the received session_id for debugging
    print("DEBUG: Stripe payment_success received session_id:", session_id)

    if not session_id or 'CHECKOUT_SESSION_ID' in str(session_id):
        # User visited page directly or success_url didn't interpolate
        return HttpResponse("Invalid or missing Stripe session ID. Please do not visit this URL directly.", status=400)

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        booking_id = session.metadata.get('booking_id')
        print("DEBUG: booking_id from session:", booking_id)
        if booking_id:
            booking = Booking.objects.filter(id=booking_id).first()
            if booking and not booking.paid:
                booking.paid = True
                booking.save()
    except Exception as e:
        print("ERROR: Stripe retrieve failed:", str(e))
        return HttpResponse("There was a problem confirming your payment. Please contact us if this keeps happening.", status=500)

    return render(request, 'users/payment_success.html', {'booking': booking})

def payment_cancel(request):
    return render(request, 'payment_cancel.html')
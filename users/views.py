from django.shortcuts import render, redirect, get_object_or_404
from events.models import Event
from .models import Participant
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator

def enter_event_code(request):
    error = None

    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            event = Event.objects.get(code__iexact=code)
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
        else:
            # Optionally: check for duplicates
            Participant.objects.create(username=username, event=event)
            return redirect('waiting_room', event_code=event.code)

    return render(request, 'users/enter_username.html', {'event': event, 'error': error})


def waiting_room(request, event_code):
    event = get_object_or_404(Event, code__iexact=event_code)
    participants = event.participants.all().order_by('joined_at')

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
        return redirect('host_dashboard')

    return redirect('host_dashboard')
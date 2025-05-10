from django.shortcuts import render, redirect, get_object_or_404
from events.models import Event
from .models import Participant

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
            return redirect('waiting_room')  # We'll build this next

    return render(request, 'users/enter_username.html', {'event': event, 'error': error})
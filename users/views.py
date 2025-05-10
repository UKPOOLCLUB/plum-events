from django.shortcuts import render, redirect, get_object_or_404
from events.models import Event

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

from django.contrib import admin
from .models import Participant, EventAvailability

admin.site.register(Participant)


@admin.register(EventAvailability)
class EventAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('date', 'status')
    list_filter = ('status',)
    ordering = ('date',)
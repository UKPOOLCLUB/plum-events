from django.contrib import admin
from .models import Participant, EventAvailability, Booking

admin.site.register(Participant)


@admin.register(EventAvailability)
class EventAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('date', 'status')
    list_filter = ('status',)
    ordering = ('date',)


class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'event_date',
        'start_time',
        'group_size',
        'quote_total',
        'paid',
        'created_at',
    )
    list_filter = ('event_date', 'paid',)
    search_fields = ('name', 'email')

admin.site.register(Booking, BookingAdmin)
from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'date', 'created_at')
    search_fields = ('name', 'code')

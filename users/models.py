from django.db import models
from django.db.models import JSONField
import uuid


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=20)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='participants')
    total_score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    kept_scores = models.JSONField(default=dict)

    class Meta:
        unique_together = ('username', 'event')

    def __str__(self):
        return self.username


class EventAvailability(models.Model):
    date = models.DateField(unique=True)
    status_choices = [
        ('available', 'Available'),
        ('full', 'Fully Booked'),
        ('blackout', 'Blackout Date'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='blackout')

    def __str__(self):
        return f"{self.date} – {self.get_status_display()}"


class Booking(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    group_size = models.PositiveIntegerField()
    selected_events = models.JSONField()  # Store as list of event names
    quote_total = models.PositiveIntegerField()
    event_date = models.DateField()
    start_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Add fields like 'contact_email', 'phone', 'special_requests' as needed

    def __str__(self):
        return f"{self.event_date} {self.start_time} – {self.group_size} people"


class ContactEnquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email}) at {self.created_at:%Y-%m-%d %H:%M}"
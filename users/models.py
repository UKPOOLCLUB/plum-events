from django.db import models
import uuid


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=20)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='participants')
    total_score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('username', 'event')

    def __str__(self):
        return self.username

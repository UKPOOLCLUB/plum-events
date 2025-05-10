from django.db import models
import uuid

class Event(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=8, unique=True)  # e.g. 4–8 letter join code
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

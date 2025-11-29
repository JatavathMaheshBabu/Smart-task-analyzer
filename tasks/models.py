from django.db import models


class TaskRecord(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=300)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(null=True, blank=True)
    importance = models.FloatField(null=True, blank=True)
    dependencies = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.id})"


from rest_framework import serializers


class TaskInputSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    title = serializers.CharField(required=True, allow_blank=False)
    due_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    estimated_hours = serializers.FloatField(required=False, allow_null=True)
    importance = serializers.FloatField(required=False, allow_null=True)
    dependencies = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

class TasksListSerializer(serializers.Serializer):
    tasks = serializers.ListSerializer(child=TaskInputSerializer())

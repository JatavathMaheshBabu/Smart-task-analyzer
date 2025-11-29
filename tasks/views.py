
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .scoring import DEFAULT_WEIGHTS, analyze_tasks, load_weights_from_config
from .serializers import TasksListSerializer

SCORING_CONFIG_PATH = getattr(settings, "SCORING_CONFIG_PATH", None) or None

class AnalyzeTasksView(APIView):
    """
    POST /api/tasks/analyze/
    Body: { "tasks": [ {..}, {...} ] }
    """
    def post(self, request):
        serializer = TasksListSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        tasks = serializer.validated_data["tasks"]
        weights = load_weights_from_config(SCORING_CONFIG_PATH) or DEFAULT_WEIGHTS
        result = analyze_tasks(tasks, weights=weights)
        if result.get("cycle"):
            return Response({"error": "circular_dependency", "cycle": result["cycle"]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)

class SuggestTasksView(APIView):
    """
    GET /api/tasks/suggest/?tasks=<urlencoded-json-array>
    or POST same body as /analyze/ - returns top 3 tasks with explanations.
    """
    def get(self, request):
        tasks_param = request.query_params.get("tasks")
        if not tasks_param:
            return Response({"error": "missing tasks parameter. Use POST /api/tasks/analyze/ instead."}, status=status.HTTP_400_BAD_REQUEST)
        import json
        try:
            tasks = json.loads(tasks_param)
        except Exception:
            return Response({"error": "invalid JSON in tasks parameter"}, status=status.HTTP_400_BAD_REQUEST)
        weights = load_weights_from_config(SCORING_CONFIG_PATH) or DEFAULT_WEIGHTS
        result = analyze_tasks(tasks, weights=weights)
        if result.get("cycle"):
            return Response({"error": "circular_dependency", "cycle": result["cycle"]}, status=status.HTTP_400_BAD_REQUEST)
        top3 = result["sorted"][:3]
        suggestions = []
        for t in top3:
            expl = t["explanation"]
            reason = f"Score {t['score']}: urgency={expl['urgency']}, importance={expl['importance']}, effort={expl['effort']}"
            suggestions.append({"id": t["id"], "title": t["title"], "score": t["score"], "reason": reason, "task": t})
        return Response({"suggestions": suggestions}, status=status.HTTP_200_OK)

# backend/tasks/urls.py
from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("analyze/", views.AnalyzeTasksView.as_view(), name="analyze"),
    path("suggest/", views.SuggestTasksView.as_view(), name="suggest"),
]

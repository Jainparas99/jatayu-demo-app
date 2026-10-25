from django.urls import path

from . import views

urlpatterns = [
    path("", views.board, name="board"),
    path("cards/edit/", views.edit_cards, name="edit-cards"),
    path("cards/schedule/", views.schedule_cards, name="schedule-cards"),
    path("cards/export/", views.download_export, name="export-cards"),
]

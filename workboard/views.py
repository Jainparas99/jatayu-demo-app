from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CardFormSet
from .services import cards_for, due_at_utc, export_cards


@login_required
@require_http_methods(["GET"])
def board(request):
    cards = cards_for(request.user, request.GET.get("status"))
    return render(request, "workboard/board.html", {"cards": list(cards)})


@login_required
@require_http_methods(["GET", "POST"])
def edit_cards(request):
    formset = CardFormSet(
        request.POST if request.method == "POST" else None, queryset=cards_for(request.user)
    )
    if request.method == "POST":
        if formset.is_valid():
            formset.save()
            return redirect("board")
        return render(request, "workboard/edit.html", {"formset": formset}, status=400)
    return render(request, "workboard/edit.html", {"formset": formset})


@login_required
@require_http_methods(["POST"])
def schedule_cards(request):
    try:
        deadline = due_at_utc(date.fromisoformat(request.POST.get("day", "")))
    except ValueError:
        return render(
            request,
            "workboard/board.html",
            {"cards": list(cards_for(request.user)), "error": "Choose a valid date."},
            status=400,
        )
    cards_for(request.user).exclude(status="done").update(due_at=deadline)
    return redirect("board")


@login_required
@require_http_methods(["GET"])
def download_export(request):
    name = export_cards(request.user)
    return FileResponse(default_storage.open(name, "rb"), as_attachment=True, filename="queue.csv")

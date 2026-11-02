from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from reports.models import SchoolClass

from .forms import NoticeForm
from .models import Notice
from .services import board_notices, invalidate_board, notices_for_class, posted_label


def board(request):
    classes = SchoolClass.objects.all()
    selected_class = None
    class_id = request.GET.get("class")
    if class_id and class_id.isdigit():
        selected_class = classes.filter(pk=class_id).first()

    notices = notices_for_class(board_notices(), selected_class)
    items = [{"notice": notice, "posted": posted_label(notice.published_at)} for notice in notices]
    return render(
        request,
        "notices/board.html",
        {"items": items, "classes": classes, "selected_class": selected_class},
    )


def detail(request, pk: int):
    notice = get_object_or_404(Notice.objects.select_related("author"), pk=pk)
    return render(request, "notices/detail.html", {"notice": notice})


@login_required
def dashboard(request):
    my_notices = (
        Notice.objects.filter(author=request.user).prefetch_related("audience").order_by("-published_at")
    )
    form_classes = request.user.form_classes.all()
    return render(
        request,
        "notices/dashboard.html",
        {"my_notices": my_notices, "form_classes": form_classes},
    )


@login_required
def create(request):
    form = NoticeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        notice = form.save(commit=False)
        notice.author = request.user
        notice.save()
        form.save_m2m()
        invalidate_board()
        messages.success(request, f"“{notice.title}” is now on the notice board.")
        return redirect("notices:dashboard")
    return render(request, "notices/form.html", {"form": form, "is_new": True})


@login_required
def edit(request, pk: int):
    notice = get_object_or_404(Notice, pk=pk, author=request.user)
    form = NoticeForm(request.POST or None, instance=notice)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"“{notice.title}” has been updated.")
        return redirect("notices:dashboard")
    return render(request, "notices/form.html", {"form": form, "notice": notice, "is_new": False})


@login_required
def delete(request, pk: int):
    notice = get_object_or_404(Notice, pk=pk, author=request.user)
    if request.method == "POST":
        title = notice.title
        notice.delete()
        invalidate_board()
        messages.success(request, f"“{title}” was taken down.")
        return redirect("notices:dashboard")
    return render(request, "notices/confirm_delete.html", {"notice": notice})

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import InterestRegistrationForm
from .models import InterestRegistration, EmailWhitelist


# Create your views here.
def index_view(request):
    if request.user.is_authenticated:
        if request.user.role == "admin":
            return redirect("admin_dashboard")
        if request.user.role in ("captain", "vice_captain"):
            return redirect("captain_dashboard")
        if request.user.role == "player":
            return redirect("player_dashboard")
    return render(request, "core/index.html")


def interest_registration_view(request):
    if request.method == "POST":
        form = InterestRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your interest has been registered successfully!")
            return redirect("interest_success")
    else:
        form = InterestRegistrationForm()
    return render(request, "core/interest_form.html", {"form": form})


def interest_success_view(request):
    return render(request, "core/interest_success.html")


@login_required
def interest_list_view(request):
    if request.user.role != "admin":
        raise PermissionDenied
    registrations = InterestRegistration.objects.all()
    return render(request, "core/interest_list.html", {"registrations": registrations})


@login_required
def update_submission_status_view(request, registration_id):
    if request.user.role != "admin":
        raise PermissionDenied
    if request.method != "POST":
        return redirect("interest_list")

    registration = get_object_or_404(InterestRegistration, id=registration_id)
    new_status = request.POST.get("status")

    if new_status not in ("approved", "rejected"):
        messages.error(request, "Invalid status value.")
        return redirect("interest_list")

    registration.status = new_status
    registration.save()

    if new_status == "approved":
        EmailWhitelist.objects.get_or_create(
            email=registration.email,
            defaults={"source": "admin", "interest_registration": registration},
        )

    messages.success(request, f"Submission status updated to {new_status}.")
    return redirect("interest_list")

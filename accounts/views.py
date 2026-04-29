from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from allauth.account.views import LoginView, SignupView, LogoutView
from .forms import CustomSignupForm
from core.models import InterestRegistration
from seasons.models import Season
from teams.models import Team


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"


class CustomSignupView(SignupView):
    template_name = "accounts/signup.html"
    form_class = CustomSignupForm


class CustomLogoutView(LogoutView):
    template_name = "accounts/logout.html"


# Create your views here.
@login_required
def admin_dashboard_view(request):
    if request.user.role != "admin":
        raise PermissionDenied
    context = {
        "pending_interest_count": InterestRegistration.objects.filter(status="pending").count(),
        "pending_team_count": Team.objects.filter(status="pending").count(),
        "active_seasons": Season.objects.filter(status="active").order_by("name"),
        "total_teams": Team.objects.filter(status="approved").count(),
    }
    return render(request, "accounts/admin_dashboard.html", context)

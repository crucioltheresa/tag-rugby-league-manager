from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from core.models import InterestRegistration
from seasons.models import Season


# Create your views here.
@login_required
def admin_dashboard_view(request):
    if request.user.role != "admin":
        raise PermissionDenied
    pending_interest_count = InterestRegistration.objects.filter(
        status="pending"
    ).count()
    # pending_team_count = request.user.teams.filter(status="pending").count()
    pending_team_count = 0
    active_season = Season.objects.filter(status="active").first()
    active_season_name = active_season.name if active_season else "No active season"
    context = {
        "pending_interest_count": pending_interest_count,
        "pending_team_count": pending_team_count,
        "active_season_name": active_season_name,
    }
    return render(request, "accounts/admin_dashboard.html", context)

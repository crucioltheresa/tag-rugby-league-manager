from django.shortcuts import redirect, render
from django.contrib import messages
from .forms import InterestRegistrationForm


# Create your views here.
class IndexView:
    def __call__(self, request):
        return render(request, "core/index.html")


index_view = IndexView()


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

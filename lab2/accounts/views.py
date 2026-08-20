from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import SignUpForm


class SignUpView(CreateView):
    """Public self-service registration for employees. Never grants staff
    access — that's reserved for the seeded admin account (see
    accounts/migrations/0002_seed_admin.py)."""

    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("reports:list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("reports:list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

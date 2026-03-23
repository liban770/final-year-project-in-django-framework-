from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from .models import User


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles or self.request.user.is_superuser

    def handle_no_permission(self):
        raise PermissionDenied("You do not have access to this page.")


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = [User.Role.ADMIN]


class SupervisorRequiredMixin(RoleRequiredMixin):
    allowed_roles = [User.Role.SUPERVISOR]


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = [User.Role.STUDENT]

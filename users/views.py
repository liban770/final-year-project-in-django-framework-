from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView

from projects.models import ActivityLog, Chapter, Notification, Project, SupervisorAssignment
from projects.forms import ContactMessageForm

from .forms import AppUserCreationForm, AppUserUpdateForm
from .mixins import AdminRequiredMixin, StudentRequiredMixin
from .models import User


class UserLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    pass


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "users/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role == User.Role.ADMIN:
            chapters = Chapter.objects.all()
            context.update(
                {
                    "total_students": User.objects.filter(role=User.Role.STUDENT).count(),
                    "total_supervisors": User.objects.filter(role=User.Role.SUPERVISOR).count(),
                    "total_projects": Project.objects.count(),
                    "pending_reviews": chapters.filter(status=Chapter.Status.PENDING).count(),
                    "approved_chapters": chapters.filter(status=Chapter.Status.APPROVED).count(),
                    "notifications_count": user.notifications.count(),
                    "recent_projects": Project.objects.select_related("student").order_by("-updated_at")[:5],
                    "recent_activities": ActivityLog.objects.select_related("user", "project").order_by("-created_at")[:6],
                }
            )
        elif user.role == User.Role.SUPERVISOR:
            assignments = SupervisorAssignment.objects.filter(supervisor=user).select_related("student")
            student_ids = assignments.values_list("student_id", flat=True)
            chapters = Chapter.objects.filter(project__student_id__in=student_ids).select_related(
                "project", "project__student"
            )
            context.update(
                {
                    "assigned_students": assignments,
                    "chapter_count": chapters.count(),
                    "total_projects": chapters.values("project_id").distinct().count(),
                    "pending_reviews": chapters.filter(status=Chapter.Status.PENDING).count(),
                    "approved_chapters": chapters.filter(status=Chapter.Status.APPROVED).count(),
                    "notifications_count": user.notifications.count(),
                    "recent_activities": ActivityLog.objects.filter(
                        Q(user=user) | Q(project__student_id__in=student_ids)
                    )
                    .select_related("user", "project")
                    .order_by("-created_at")[:6],
                }
            )
        else:
            project = Project.objects.filter(student=user).first()
            chapters = Chapter.objects.filter(project=project) if project else Chapter.objects.none()
            chapter_count = chapters.count()
            expected_chapters = 5
            progress_percent = min(100, int((chapter_count / expected_chapters) * 100)) if expected_chapters else 0
            context.update(
                {
                    "project": project,
                    "chapters": chapters.order_by("-submission_date"),
                    "total_projects": 1 if project else 0,
                    "pending": chapters.filter(status=Chapter.Status.PENDING).count(),
                    "reviewed": chapters.filter(status=Chapter.Status.REVIEWED).count(),
                    "approved": chapters.filter(status=Chapter.Status.APPROVED).count(),
                    "approved_chapters": chapters.filter(status=Chapter.Status.APPROVED).count(),
                    "notifications_count": user.notifications.count(),
                    "chapter_count": chapter_count,
                    "expected_chapters": expected_chapters,
                    "progress_percent": progress_percent,
                    "progress_text": f"{chapter_count}/{expected_chapters}",
                    "recent_activities": ActivityLog.objects.filter(
                        Q(user=user) | Q(project__student=user)
                    )
                    .select_related("project")
                    .order_by("-created_at")[:6],
                }
            )

        context["unread_notifications"] = user.notifications.filter(is_read=False)[:8]
        context["notifications"] = user.notifications.all()[:20]
        return context


class UserCreateView(AdminRequiredMixin, CreateView):
    template_name = "users/create_user.html"
    form_class = AppUserCreationForm
    success_url = reverse_lazy("users:user-list")


class AdminUserListView(AdminRequiredMixin, TemplateView):
    template_name = "users/user_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.order_by("role", "username")
        return context


class AdminUserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    template_name = "users/user_edit.html"
    form_class = AppUserUpdateForm
    success_url = reverse_lazy("users:user-list")

    def get_queryset(self):
        # Admin can edit any user except themselves deletion is handled separately.
        return User.objects.all()


class AdminUserDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        if request.POST.get("confirm") != "yes":
            messages.error(request, "Deletion confirmation missing.")
            return redirect("users:user-list")
        user_to_delete = get_object_or_404(User, pk=pk)
        if user_to_delete == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect("users:user-list")

        user_to_delete.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("users:user-list")


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return redirect("users:dashboard")


class NotificationDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        if request.POST.get("confirm") != "yes":
            messages.error(request, "Deletion confirmation missing.")
            return redirect("users:dashboard")
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.delete()
        messages.success(request, "Notification deleted.")
        return redirect("users:dashboard")


class NotificationClearAllView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if request.POST.get("confirm") != "yes":
            messages.error(request, "Deletion confirmation missing.")
            return redirect("users:dashboard")
        Notification.objects.filter(user=request.user).delete()
        messages.success(request, "All notifications cleared.")
        return redirect("users:dashboard")


def role_redirect_view(request):
    if not request.user.is_authenticated:
        return redirect("users:login")
    return redirect("users:dashboard")


class HomePageView(TemplateView):
    template_name = "users/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        return super().dispatch(request, *args, **kwargs)


class AboutPageView(TemplateView):
    template_name = "users/about.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        return super().dispatch(request, *args, **kwargs)


class ContactPageView(CreateView):
    template_name = "users/contact.html"
    form_class = ContactMessageForm
    success_url = reverse_lazy("users:contact")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Thank you for your message! We'll get back to you soon.")
        return super().form_valid(form)

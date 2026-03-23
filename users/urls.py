from django.urls import path

from .views import (
    AdminUserDeleteView,
    AdminUserListView,
    AdminUserUpdateView,
    DashboardView,
    NotificationClearAllView,
    NotificationDeleteView,
    NotificationMarkReadView,
    UserCreateView,
    UserLoginView,
    UserLogoutView,
    role_redirect_view,
)

app_name = "users"

urlpatterns = [
    path("", role_redirect_view, name="home"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("create-user/", UserCreateView.as_view(), name="create-user"),
    path("users/", AdminUserListView.as_view(), name="user-list"),
    path("users/<int:pk>/edit/", AdminUserUpdateView.as_view(), name="user-edit"),
    path("users/<int:pk>/delete/", AdminUserDeleteView.as_view(), name="user-delete"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification-read"),
    path("notifications/<int:pk>/delete/", NotificationDeleteView.as_view(), name="notification-delete"),
    path("notifications/clear/", NotificationClearAllView.as_view(), name="notification-clear"),
]

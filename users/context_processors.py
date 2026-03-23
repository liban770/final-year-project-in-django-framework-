from .models import User
from .models import Notification

def unread_notification_count(request):
    """
    Provides `unread_notification_count` to all templates for the navbar badge.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"unread_notification_count": 0}

    # Import lazily to avoid circular imports.
    from projects.models import Notification

    return {
        "unread_notification_count": Notification.objects.filter(user=user, is_read=False).count()
        if user.role in {User.Role.ADMIN, User.Role.SUPERVISOR, User.Role.STUDENT}
        else 0
    }


def unread_notification_preview(request):
    """
    Provides a small list of unread notifications for the navbar dropdown.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"unread_notifications_nav": []}

    unread_qs = Notification.objects.filter(user=user, is_read=False).order_by("-created_at")[:5]
    return {"unread_notifications_nav": unread_qs}


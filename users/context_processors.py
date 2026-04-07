from .models import Notification


def unread_notifications(request):
    """
    Makes the count of unread notifications available in all templates
    for authenticated users.
    """
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {"unread_notifications_count": count}

    return {"unread_notifications_count": 0}

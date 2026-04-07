"""
This module defines the database models for the 'users' app.
It includes the custom user model to support role-based authentication, 
a notification system, and student-specific preference profiles.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Customizes the default Django User model to include a 'role' field.
    This allows the application to differentiate between students, owners, and admins.
    """
    # Define available roles for users in the system
    ROLE_CHOICES = (
        ("student", "Student"),
        ("owner", "Owner"),
        ("admin", "Admin"),
    )
    # The role of the user, defaulting to 'student'
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")

    # Override email field
    email = models.EmailField(unique=True)

    def __str__(self):
        """Returns a readable string representation of the user, including their role."""
        return f"{self.username} ({self.get_role_display()})"


class Notification(models.Model):
    """
    Represents an in-app notification sent to a specific user.
    Used for alerting students when waitlisted beds become available, etc.
    """
    # The user receiving the notification. Related name allows `user.notifications.all()`
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="notifications"
    )
    # The actual text content of the notification alert
    message = models.TextField()
    # Tracks whether the user has viewed this notification yet
    is_read = models.BooleanField(default=False)
    # An optional URL that the notification can link to when clicked
    link = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="URL to redirect to when clicked",
    )
    # Automatically records the date and time the notification was generated
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Orders notifications so the newest ones appear at the top of the list
        ordering = ["-created_at"]

    def __str__(self):
        """Returns a string representing the notification for admin panels."""
        return f"Notification for {self.user.username}: {self.message[:20]}"


class StudentProfile(models.Model):
    """
    An extension of the CustomUser model specifically for Students.
    Stores their target budget, dietary needs, and required amenities to help provide 'Smart Matches'.
    """
    # 1-to-1 link back to the CustomUser. If the user is deleted, this profile is deleted too.
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="student_profile"
    )

    # Budget and location preferences
    # The maximum amount the student is willing to spend per month
    target_budget = models.IntegerField(
        null=True, blank=True, help_text="Maximum monthly budget"
    )

    # Dietary preferences
    # Choices allow matching the student with Messes that serve their specific diet
    DIET_CHOICES = (("any", "Any"), ("veg", "Pure Veg"), ("jain", "Jain Food Only"))
    preferred_food = models.CharField(
        max_length=10, choices=DIET_CHOICES, default="any"
    )

    # Amenity preferences for matching with PGs
    # Whether the student strictly requires Air Conditioning
    requires_ac = models.BooleanField(default=False)
    # Whether the student strictly requires WiFi connectivity
    requires_wifi = models.BooleanField(default=False)
    # Whether the student strictly requires an attached (private) bathroom
    requires_bathroom = models.BooleanField(default=False)

    def __str__(self):
        """Returns a readable string identifying whose preferences these are."""
        return f"Preferences for {self.user.username}"

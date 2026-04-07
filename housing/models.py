from django.db import models
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from users.models import Notification

User = get_user_model()


class PG(models.Model):
    """
    Represents a Paying Guest (PG) accommodation listing.
    Stores all physical details, pricing, amenities, and geographical data.
    """
    # The owner who created this listing. Related name allows `owner.pgs.all()`
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "owner"},
        related_name="pgs",
    )
    name = models.CharField(max_length=200)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)

    # --- Filters ---
    gender_restriction = models.CharField(
        max_length=20,
        choices=(("boys", "Boys only"), ("girls", "Girls only"), ("any", "Anyone")),
        default="any",
        db_index=True,
    )
    food_included = models.BooleanField(default=False, db_index=True)
    has_wifi = models.BooleanField(default=False)
    has_ac = models.BooleanField(default=False)
    attached_bathroom = models.BooleanField(default=False)

    # Pricing info
    starting_price = models.DecimalField(max_digits=8, decimal_places=2, db_index=True)

    image = models.ImageField(upload_to="pg_images/", blank=True, null=True)

    # Coordinates for interactive maps
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.owner.username}"


class Room(models.Model):
    """
    Represents a specific room inside a PG.
    Because one PG can have multiple rooms (Single, Double, etc.), this has a ForeignKey to PG.
    """
    pg = models.ForeignKey(PG, on_delete=models.CASCADE, related_name="rooms")
    occupancy = models.IntegerField(
        choices=((1, "Single"), (2, "Double"), (3, "Triple"), (4, "Quad")), default=2
    )
    rent_per_month = models.DecimalField(max_digits=8, decimal_places=2)
    vacant_beds = models.IntegerField(default=2)

    @property
    def is_available(self):
        """Returns True if there is at least one vacant bed in this room."""
        return self.vacant_beds > 0

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to handle:
        1. Defaulting vacant_beds to occupancy on creation.
        2. Yield management: Triggering notifications if a bed frees up.
        """
        is_new = self.pk is None
        old_vacant_beds = 0

        if not is_new:
            old_vacant_beds = Room.objects.get(pk=self.pk).vacant_beds

        # On creation, default vacant_beds to occupancy if not explicitly set
        if is_new and self.vacant_beds == 2 and self.occupancy != 2:
            self.vacant_beds = self.occupancy

        super().save(*args, **kwargs)

        # Yield Management: If beds just became available, notify someone!
        if self.vacant_beds > old_vacant_beds:
            from django.utils import timezone

            # Find the top person waiting
            next_in_line = (
                self.pg.waitlists.filter(status="waiting")
                .filter(
                    models.Q(room_type_preference__isnull=True)
                    | models.Q(room_type_preference=self.occupancy)
                )
                .order_by("joined_at")
                .first()
            )

            if next_in_line:
                next_in_line.status = "notified"
                next_in_line.notified_at = timezone.now()
                next_in_line.save()

                # 1. Create In-App Notification
                message = f"Good news! A {self.get_occupancy_display()} bed is now available at {self.pg.name}."
                Notification.objects.create(
                    user=next_in_line.student,
                    message=message,
                    link=f"/pgs/{self.pg.id}/",
                )

                # 2. Send Email Notification
                subject = f"Waitlist Alert: Bed available at {self.pg.name}"
                email_body = (
                    f"Hello {next_in_line.student.username},\n\n"
                    f"A {self.get_occupancy_display()} sharing bed has just opened up at {self.pg.name}.\n"
                    f"Log in to RoomAndRoti and check it out!\n\n"
                    f"Thanks,\nRoomAndRoti Team"
                )

                send_mail(
                    subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL
                    if hasattr(settings, "DEFAULT_FROM_EMAIL")
                    else "noreply@roomandroti.local",
                    [next_in_line.student.email],
                    fail_silently=False,
                )

    def __str__(self):
        return f"{self.get_occupancy_display()} sharing at {self.pg.name}"


class Waitlist(models.Model):
    """
    Represents a queue for students waiting for a room to become available in a specific PG.
    """
    STATUS_CHOICES = (
        ("waiting", "Waiting"),
        ("notified", "Notified"),
        ("resolved", "Resolved (Joined/Declined)"),
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        related_name="waitlists",
    )
    pg = models.ForeignKey(PG, on_delete=models.CASCADE, related_name="waitlists")
    room_type_preference = models.IntegerField(
        choices=((1, "Single"), (2, "Double"), (3, "Triple"), (4, "Quad")),
        null=True,
        blank=True,
        help_text="Specific room type they want",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")
    joined_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["joined_at"]  # First-in, first-out queue
        unique_together = [
            "student",
            "pg",
        ]  # Can only be on the waitlist for a specific PG once

    def __str__(self):
        return f"{self.student.username} waiting for {self.pg.name}"


class ListingView(models.Model):
    """
    Basic analytics model to track views on PGs and Messes.
    """

    LISTING_TYPE_CHOICES = (("pg", "PG"), ("mess", "Mess"))

    listing_type = models.CharField(max_length=4, choices=LISTING_TYPE_CHOICES)
    listing_id = models.IntegerField()
    viewed_at = models.DateTimeField(default=timezone.now)

    # Store user if logged in, otherwise track anonymously
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["listing_type", "listing_id", "viewed_at"]),
        ]

    def __str__(self):
        return f"{self.get_listing_type_display()} {self.listing_id} viewed at {self.viewed_at}"

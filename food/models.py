from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Mess(models.Model):
    """
    Represents a Mess or Tiffin service listing.
    Stores the owner details, location, pricing, and exact dietary tags (Veg, Jain, etc.).
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "owner"},
        related_name="messes",
    )
    name = models.CharField(max_length=200)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)

    # Pricing
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2, db_index=True)
    single_meal_fee = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )

    # Dietary Flags
    is_veg_only = models.BooleanField(default=False, db_index=True)
    has_jain_food = models.BooleanField(default=False, db_index=True)
    has_non_veg = models.BooleanField(default=False, db_index=True)

    image = models.ImageField(upload_to="mess_images/", blank=True, null=True)

    # Coordinates for interactive maps
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum([r.rating for r in ratings]) / ratings.count(), 1)
        return 0.0

    @property
    def rating_count(self):
        return self.ratings.count()


class DailyMenu(models.Model):
    """
    Represents the specific Breakfast, Lunch, and Dinner menu for a single Mess on a single day.
    """
    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name="daily_menus")
    date = models.DateField(auto_now_add=True)
    breakfast_items = models.TextField(
        blank=True, help_text="List items on separate lines"
    )
    lunch_items = models.TextField(blank=True, help_text="List items on separate lines")
    dinner_items = models.TextField(
        blank=True, help_text="List items on separate lines"
    )

    class Meta:
        unique_together = ("mess", "date")

    def __str__(self):
        return f"{self.mess.name} - {self.date}"


class MessRating(models.Model):
    """
    Represents a user's rating and review for a Mess.
    """
    mess = models.ForeignKey(Mess, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mess_ratings")
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mess', 'user')

    def __str__(self):
        return f"{self.user.username}'s {self.rating}-star rating for {self.mess.name}"

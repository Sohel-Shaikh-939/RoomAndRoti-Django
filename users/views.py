"""
This module contains backend logic (views) for managing users,
including registration, profiles, notifications, and the owner analytics dashboard.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from housing.models import ListingView
from django.db.models import Count
from django.db.models.functions import TruncDate
from .forms import StudentRegistrationForm, OwnerRegistrationForm, StudentProfileForm
from .models import StudentProfile


def register_view(request):
    """
    Handles new user registration for both Students and Owners.
    Validates form data, saves the user, and automatically logs them in.
    """
    if request.method == "POST":
        # Check the 'role' submitted in the form to determine which validation to use
        role = request.POST.get("role", "student")
        if role == "owner":
            form = OwnerRegistrationForm(request.POST)
        else:
            form = StudentRegistrationForm(request.POST)

        # Validate the submitted data (e.g., matching passwords, unique usernames)
        if form.is_valid():
            # Save the new user to the database
            user = form.save()
            # Immediately authenticate and log the user into the current session
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            
            # Send a success flash message to the UI
            messages.success(
                request, f"Welcome, {user.username}! Your account has been created."
            )
            # Redirect them back to the site homepage
            return redirect("home")
    else:
        # For initial GET requests, load the blank student form by default
        form = StudentRegistrationForm()

    # Render the registration HTML template
    return render(request, "users/register.html", {"form": form})


@login_required # Forces the user to be logged in to view this page
def dashboard_view(request):
    """
    Displays the analytics dashboard for property owners.
    Calculates total views across all their PG and Mess listings and generates data 
    for visual charts showing the last 7 days of traffic.
    """
    # Authorization Check: Kick non-owners back to the homepage
    if request.user.role != "owner":
        messages.error(request, "Only Owners have access to the dashboard.")
        return redirect("home")

    # Fetch all PG and Mess listings attached to the currently logged in owner
    pgs = request.user.pgs.all()
    messes = request.user.messes.all()

    # Extract just the primary key IDs into flat lists (e.g., [1, 2, 5]) for fast database filtering
    pg_ids = pgs.values_list("id", flat=True)
    mess_ids = messes.values_list("id", flat=True)

    # 1. Total All-Time Views
    # Count how many total ListingView hit records match any of the owner's PG IDs
    total_pg_views = ListingView.objects.filter(
        listing_type="pg", listing_id__in=pg_ids
    ).count()
    # Count how many total ListingView hit records match any of the owner's Mess IDs
    total_mess_views = ListingView.objects.filter(
        listing_type="mess", listing_id__in=mess_ids
    ).count()

    # 2. Daily Views for Charts (Last 7 Days)
    # Calculate the exact date 7 days ago
    start_date = timezone.now().date() - timedelta(days=6)

    # Database query to aggregate PG views per day:
    # - filter(): Get only views from the last 7 days for the owner's PGs
    # - annotate(date...): Strip the exact time, grouping strictly by the Day
    # - values('date').annotate(count...): Count the total views for each specific Day
    pg_views_by_date = (
        ListingView.objects.filter(
            listing_type="pg", listing_id__in=pg_ids, viewed_at__date__gte=start_date
        )
        .annotate(date=TruncDate("viewed_at"))
        .values("date")
        .annotate(count=Count("id"))
    )

    # Do the exact same daily aggregation for Mess views
    mess_views_by_date = (
        ListingView.objects.filter(
            listing_type="mess",
            listing_id__in=mess_ids,
            viewed_at__date__gte=start_date,
        )
        .annotate(date=TruncDate("viewed_at"))
        .values("date")
        .annotate(count=Count("id"))
    )

    # Convert the raw database query output into clean dictionary lookups
    # Format: { '2023-11-01': 15, '2023-11-02': 22 }
    pg_views_dict = {item["date"]: item["count"] for item in pg_views_by_date}
    mess_views_dict = {item["date"]: item["count"] for item in mess_views_by_date}

    labels = []
    pg_data = []
    mess_data = []

    # Loop backwards from 6 days ago moving forward to today
    # This ensures the chart X-axis is built in chronological order
    for i in range(6, -1, -1):
        target_date = timezone.now().date() - timedelta(days=i)

        # Format the date nicely for the frontend (e.g., 'Oct 15')
        labels.append(target_date.strftime("%b %d"))

        # Look up the view count for this specific day using `.get()`
        # If there were no views that day, it safely returns 0 instead of throwing an error
        pg_data.append(pg_views_dict.get(target_date, 0))
        mess_data.append(mess_views_dict.get(target_date, 0))

    # Send all this calculated data to the template rendering engine
    return render(
        request,
        "users/dashboard.html",
        {
            "pgs": pgs,
            "messes": messes,
            "total_pg_views": total_pg_views,
            "total_mess_views": total_mess_views,
            "chart_labels": labels, # X-Axis
            "chart_pg_data": pg_data, # Data series 1
            "chart_mess_data": mess_data, # Data series 2
        },
    )


@login_required
def profile_view(request):
    """
    Displays and allows users to update their personal profiles and preferences.
    Students have an extended profile for budget and diet needs.
    """
    if request.user.role == "student":
        # Ensure a StudentProfile exists. get_or_create prevents crashes if it wasn't made during registration.
        profile, created = StudentProfile.objects.get_or_create(user=request.user)

        if request.method == "POST":
            # Bind the submitted POST data to the existing database profile instance
            form = StudentProfileForm(request.POST, instance=profile)
            if form.is_valid():
                # Save the updated preferences to the database
                form.save()
                messages.success(
                    request,
                    "Your preferences have been updated! Check the homepage for new Smart Matches.",
                )
                # Refresh the page to show the successful state
                return redirect("profile")
        else:
            # Pre-fill the form with the student's current saved preferences
            form = StudentProfileForm(instance=profile)

        return render(
            request, "users/profile.html", {"user": request.user, "form": form}
        )
    else:
        # Owners don't currently have an extended profile, just show basic CustomUser info
        return render(request, "users/profile.html", {"user": request.user})


@login_required
def notifications_list(request):
    """
    Fetches all notifications for the user, displays them, 
    and automatically marks any unread notifications as read.
    """
    # Grab every notification linked to this user's account via the foreign key
    notifications = request.user.notifications.all()

    # Filter out only the ones that haven't been seen yet
    unread_notifications = notifications.filter(is_read=False)
    
    # If there are any unread ones, run a fast bulk-update query to mark them as True
    # .update() is highly optimized compared to looping and saving individually
    if unread_notifications.exists():
        unread_notifications.update(is_read=True)

    # Pass the full list (both read and newly-read) to the template
    return render(
        request, "users/notifications_list.html", {"notifications": notifications}
    )

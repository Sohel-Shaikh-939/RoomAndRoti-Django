"""
URL configuration for the 'users' app.
Maps URL patterns to their respective view functions or classes.
"""
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Uses Django's built-in LoginView, but points it to our custom template
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    
    # Uses Django's built-in LogoutView and redirects the user back to the login page after success
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    
    # Custom registration view supporting both students and owners
    path("register/", views.register_view, name="register"),
    
    # The analytics dashboard restricted to users with the 'owner' role
    path("dashboard/", views.dashboard_view, name="owner_dashboard"),
    
    # User profile page to manage preferences and personal info
    path("profile/", views.profile_view, name="profile"),
    
    # Page to view unread system-generated notifications
    path("notifications/", views.notifications_list, name="notifications"),
    
    # --- Password Reset URLs (Django Built-in Auth Views) ---
    # Step 1: Form to request a password reset email
    path("password_reset/", auth_views.PasswordResetView.as_view(
        template_name="users/password_reset_form.html",
        email_template_name="users/password_reset_email.html",
        subject_template_name="users/password_reset_subject.txt"
    ), name="password_reset"),
    
    # Step 2: Confirmation page shown after submitting the email form
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="users/password_reset_done.html"
    ), name="password_reset_done"),
    
    # Step 3: The actual form where the user types their new password (uses the secure link from their email)
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="users/password_reset_confirm.html"
    ), name="password_reset_confirm"),
    
    # Step 4: Success page confirming the password was changed successfully
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="users/password_reset_complete.html"
    ), name="password_reset_complete"),
]

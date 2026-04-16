"""
URL configuration for the 'food' app.
Maps URL patterns to their respective view functions for finding and managing Messes.
"""
from django.urls import path
from . import views

urlpatterns = [
    # --- Mess Listing Main URLs ---
    path("", views.mess_list, name="mess_list"), # Main page showing all available messes
    path("add/", views.add_mess, name="add_mess"), # Page for an owner to add a new mess
    path("<int:pk>/", views.mess_detail, name="mess_detail"), # Detail view for a specific mess
    path("<int:mess_id>/rate/", views.rate_mess, name="rate_mess"), # Endpoint for submitting rating
    path("<int:pk>/edit/", views.edit_mess, name="edit_mess"), # Form for editing an existing mess
    
    # --- Daily Menu URLs ---
    path("<int:mess_id>/update-menu/", views.update_daily_menu, name="update_menu"), # Owners updating daily food items
]

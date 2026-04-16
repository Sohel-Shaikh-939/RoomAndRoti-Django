"""
URL configuration for the 'housing' app.
Maps URL patterns to their respective view functions for managing PGs, rooms, and waitlists.
"""
from django.urls import path
from . import views

urlpatterns = [
    # --- PG Listing Main URLs ---
    path("", views.pg_list, name="pg_list"), # Displays the main list of all PGs with filters
    path("add/", views.add_pg, name="add_pg"), # Form view for owners to create a new PG
    path("<int:pk>/", views.pg_detail, name="pg_detail"), # Detailed view for a single specific PG
    path("<int:pg_id>/rate/", views.rate_pg, name="rate_pg"), # Endpoint for submitting rating
    path("<int:pk>/edit/", views.edit_pg, name="edit_pg"), # Form view for owners to edit PG details
    path("compare/", views.compare_pgs, name="compare_pgs"), # Specialized tool to compare multiple PGs
    
    # --- Automated Waitlist URLs ---
    path("<int:pg_id>/waitlist/join/", views.join_waitlist, name="join_waitlist"), # Endpoint for students to enter a queue
    path("waitlists/manage/", views.manage_waitlists, name="manage_waitlists"), # Dashboard for owners to view who is waiting
    
    # --- Room Management URLs (Owner specific) ---
    path("<int:pg_id>/rooms/", views.manage_rooms, name="manage_rooms"), # Shows all rooms inside a specific PG
    path("<int:pg_id>/rooms/add/", views.add_room, name="add_room"), # Form to create a new room (e.g., a "Double Sharing")
    path("rooms/<int:room_id>/edit/", views.edit_room, name="edit_room"), # Form to edit rent/occupancy of an existing room
    path("rooms/<int:room_id>/delete/", views.delete_room, name="delete_room"), # Deletes a specific room entirely
]

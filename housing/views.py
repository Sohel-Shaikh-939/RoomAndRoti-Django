from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import PG, Waitlist, Room, ListingView, PGRating
from django.utils import timezone
from .forms import PGForm, RoomForm

from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points on the earth.
    Uses the Haversine formula, which accounts for the Earth's curvature.
    This enables the 'Find PGs Near Me' functionality.
    """
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

def pg_list(request):
    """
    Displays a paginated list of all PGs.
    Handles dynamic GET filtering based on search queries, budget limits, gender rules, 
    amenities, and geo-location distance sorting.
    """
    # Fetch all PGs, optimizing with select_related to avoid N+1 queries on the owner database hits
    pgs = PG.objects.select_related("owner").all().order_by("-created_at")

    # Apply search filter across PG name and address
    q = request.GET.get("q")
    if q:
        pgs = pgs.filter(Q(name__icontains=q) | Q(address__icontains=q))

    # Basic filtering
    budget = request.GET.get("budget")
    gender = request.GET.get("gender")
    food = request.GET.get("food")

    if budget:
        pgs = pgs.filter(starting_price__lte=budget)
    if gender and gender != "any":
        # Strictly match gender restrictions (i.e. 'boys' shows Boys Only)
        pgs = pgs.filter(gender_restriction=gender)
    if food:
        pgs = pgs.filter(food_included=True)

    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius")

    if lat and lng:
        try:
            user_lat = float(lat)
            user_lng = float(lng)
            # Default to 10km if not specified
            radius_km = float(radius) if radius else 10.0
            
            pg_list_filtered = []
            
            for pg in pgs:
                if pg.latitude is not None and pg.longitude is not None:
                    dist = haversine(user_lng, user_lat, pg.longitude, pg.latitude)
                    # Only include if within radius
                    if dist <= radius_km:
                        pg.distance = dist
                        pg_list_filtered.append(pg)
                else:
                    # If no coordinates, we can't calculate distance, 
                    # so we exclude it from "nearby" results
                    pass
                    
            # Sort the filtered list by distance (closest first)
            pgs = sorted(pg_list_filtered, key=lambda x: x.distance)
        except ValueError:
            pass

    # Pagination
    paginator = Paginator(pgs, 6)  # 6 PGs per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "housing/pg_list.html", {"pgs": page_obj})


def pg_detail(request, pk):
    """Displays detailed information for a single PG and records an analytics view."""
    pg = get_object_or_404(PG, pk=pk)

    # Record analytics view
    viewer = request.user if request.user.is_authenticated else None
    ListingView.objects.create(listing_type="pg", listing_id=pg.id, viewer=viewer)

    return render(request, "housing/pg_detail.html", {"pg": pg})


@login_required
def add_pg(request):
    """Allows owners to create and list a new PG."""
    # Restrict to owners only
    if request.user.role != "owner":
        messages.error(request, "Only owners can add PGs.")
        return redirect("home")

    if request.method == "POST":
        form = PGForm(request.POST, request.FILES)
        if form.is_valid():
            pg = form.save(commit=False)
            pg.owner = request.user
            pg.save()
            messages.success(request, f"Successfully added {pg.name}!")
            return redirect("owner_dashboard")
    else:
        form = PGForm()

    return render(request, "housing/add_pg.html", {"form": form})


@login_required
def edit_pg(request, pk):
    """Allows owners to update details of an existing PG they own."""
    pg = get_object_or_404(PG, pk=pk)

    if request.user != pg.owner:
        messages.error(request, "You do not have permission to edit this PG.")
        return redirect("owner_dashboard")

    if request.method == "POST":
        form = PGForm(request.POST, request.FILES, instance=pg)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated {pg.name}!")
            return redirect("owner_dashboard")
    else:
        form = PGForm(instance=pg)

    return render(request, "housing/edit_pg.html", {"form": form, "pg": pg})


def compare_pgs(request):
    """
    Displays a side-by-side comparison of up to 3 selected PGs.
    Extracts the 'id' parameters from the GET request URL and filters the database.
    """
    # Retrieve the list of PG IDs from the URL query parameters (e.g. ?id=1&id=2)
    pg_ids = request.GET.getlist("id")
    # Limit to 3 PGs for comparison to keep the UI clean
    pg_ids = pg_ids[:3]

    if len(pg_ids) < 2:
        messages.error(request, "Please select at least 2 PGs to compare.")
        return redirect("pg_list")

    pgs = PG.objects.filter(id__in=pg_ids)
    return render(request, "housing/compare_pgs.html", {"pgs": pgs})


@login_required
def join_waitlist(request, pg_id):
    """
    Allows a student to join the waitlist for a specific PG.
    Checks if they are already on the list before adding them.
    Triggered when a PG has no available beds.
    """
    # Restrict this action to students only so Owners cannot pollute the waitlists
    if request.user.role != "student":
        messages.error(request, "Only students can join waitlists.")
        return redirect("pg_detail", pk=pg_id)

    pg = get_object_or_404(PG, pk=pg_id)

    if Waitlist.objects.filter(student=request.user, pg=pg).exists():
        messages.info(request, "You are already on the waitlist for this PG.")
        return redirect("pg_detail", pk=pg_id)

    if request.method == "POST":
        room_type = request.POST.get("room_type_preference")
        if room_type:
            room_type = int(room_type)

        Waitlist.objects.create(
            student=request.user, pg=pg, room_type_preference=room_type
        )
        messages.success(
            request, f"You have successfully joined the waitlist for {pg.name}!"
        )
        return redirect("pg_detail", pk=pg_id)

    return redirect("pg_detail", pk=pg_id)


@login_required
def manage_waitlists(request):
    """
    Allows owners to view all students currently waitlisted for their properties.
    """
    if request.user.role != "owner":
        messages.error(request, "Only owners can manage waitlists.")
        return redirect("home")

    # Get all waitlists for PGs owned by this user
    # Uses select_related to grab the PG and Student data in a single SQL Join query
    waitlists = (
        Waitlist.objects.select_related("pg", "student")
        .filter(pg__owner=request.user)
        .order_by("pg", "joined_at")
    )

    return render(request, "housing/manage_waitlists.html", {"waitlists": waitlists})


@login_required
def manage_rooms(request, pg_id):
    """Displays all rooms associated with a specific PG for the owner to manage."""
    if request.user.role != "owner":
        messages.error(request, "Only owners can manage rooms.")
        return redirect("home")

    pg = get_object_or_404(PG, pk=pg_id)
    if pg.owner != request.user:
        messages.error(request, "You do not own this PG.")
        return redirect("owner_dashboard")

    rooms = pg.rooms.all().order_by("occupancy")
    return render(request, "housing/manage_rooms.html", {"pg": pg, "rooms": rooms})


@login_required
def add_room(request, pg_id):
    """Allows an owner to add a new room configuration to a specific PG."""
    if request.user.role != "owner":
        messages.error(request, "Only owners can add rooms.")
        return redirect("home")

    pg = get_object_or_404(PG, pk=pg_id)
    if pg.owner != request.user:
        messages.error(request, "You do not own this PG.")
        return redirect("owner_dashboard")

    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.pg = pg
            room.save()
            messages.success(
                request, f"Successfully added a {room.get_occupancy_display()} room!"
            )
            return redirect("manage_rooms", pg_id=pg.id)
    else:
        form = RoomForm()

    return render(
        request, "housing/room_form.html", {"form": form, "pg": pg, "action": "Add"}
    )


@login_required
def edit_room(request, room_id):
    """Allows an owner to modify an existing room configuration."""
    if request.user.role != "owner":
        messages.error(request, "Only owners can edit rooms.")
        return redirect("home")

    room = get_object_or_404(Room, pk=room_id)
    pg = room.pg

    if pg.owner != request.user:
        messages.error(request, "You do not own this PG.")
        return redirect("owner_dashboard")

    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully updated the room!")
            return redirect("manage_rooms", pg_id=pg.id)
    else:
        form = RoomForm(instance=room)

    return render(
        request,
        "housing/room_form.html",
        {"form": form, "pg": pg, "room": room, "action": "Edit"},
    )


@login_required
def delete_room(request, room_id):
    """Allows an owner to delete a room from their PG."""
    if request.user.role != "owner":
        messages.error(request, "Only owners can delete rooms.")
        return redirect("home")

    room = get_object_or_404(Room, pk=room_id)
    pg = room.pg

    if pg.owner != request.user:
        messages.error(request, "You do not own this PG.")
        return redirect("owner_dashboard")

    if request.method == "POST":
        room.delete()
        messages.success(request, "Room successfully deleted!")
        return redirect("manage_rooms", pg_id=pg.id)

    # In case of GET request, usually we redirect or show an error
    return redirect("manage_rooms", pg_id=pg.id)


@login_required
def rate_pg(request, pg_id):
    """
    Submits a user rating for a PG.
    Restricts rating to users who have been registered for over 60 days.
    """
    if request.method == "POST":
        pg = get_object_or_404(PG, pk=pg_id)
        
        # Prevent owners from rating their own PG
        if request.user == pg.owner:
            messages.error(request, "You cannot rate your own listing.")
            return redirect("pg_detail", pk=pg_id)
            
        # Account Age Check: Must be >= 60 days
        account_age = (timezone.now() - request.user.date_joined).days
        if account_age < 60:
            messages.error(request, "Your account must be at least 2 months old to leave a rating.")
            return redirect("pg_detail", pk=pg_id)
            
        rating_value = request.POST.get("rating")
        comment = request.POST.get("comment", "")
        
        if rating_value and rating_value.isdigit() and 1 <= int(rating_value) <= 5:
            # Create or update the rating
            rating, created = PGRating.objects.update_or_create(
                pg=pg,
                user=request.user,
                defaults={"rating": int(rating_value), "comment": comment}
            )
            messages.success(request, "Your rating has been submitted successfully!")
            return redirect("pg_detail", pk=pg_id)
        else:
            messages.error(request, "Invalid rating value.")
            
    return redirect("pg_detail", pk=pg_id)

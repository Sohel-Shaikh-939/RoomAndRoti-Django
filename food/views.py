from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Mess, DailyMenu
from .forms import MessForm
from housing.models import ListingView
from datetime import date
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

def mess_list(request):
    """
    Displays a paginated list of all Messes.
    Allows students to search by location/name, and strictly filter by exact dietary needs
    like 'Pure Veg' or 'Jain Food Only'. It also supports geo-location sorting.
    """
    # Fetch all Messes, optimizing with select_related to avoid N+1 queries on the owner database hit
    messes = Mess.objects.select_related("owner").all().order_by("-created_at")

    # Search by location or name
    q = request.GET.get("q")
    if q:
        messes = messes.filter(Q(name__icontains=q) | Q(address__icontains=q))

    # Dietary filtering
    diet = request.GET.get("diet")
    if diet == "veg":
        messes = messes.filter(is_veg_only=True)
    elif diet == "jain":
        messes = messes.filter(has_jain_food=True)
    elif diet == "nonveg":
        messes = messes.filter(has_non_veg=True)

    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius")

    if lat and lng:
        try:
            user_lat = float(lat)
            user_lng = float(lng)
            # Default to 10km if not specified
            radius_km = float(radius) if radius else 10.0
            
            mess_list_filtered = []
            
            for mess in messes:
                if mess.latitude is not None and mess.longitude is not None:
                    dist = haversine(mess.longitude, mess.latitude, user_lng, user_lat)
                    # Only include if within radius
                    if dist <= radius_km:
                        mess.distance = dist
                        mess_list_filtered.append(mess)
                else:
                    # If no coordinates, exclude from nearby results
                    pass
                    
            # Sort the filtered list by distance (closest first)
            messes = sorted(mess_list_filtered, key=lambda x: x.distance)
        except ValueError:
            pass

    # Pagination
    paginator = Paginator(messes, 6)  # 6 Messes per page
    page_number = request.GET.get("page")
    messes_page = paginator.get_page(page_number)

    return render(request, "food/mess_list.html", {"messes": messes_page})


def mess_detail(request, pk):
    """Displays detailed information for a single Mess, today's menu, and records an analytics view."""
    mess = get_object_or_404(Mess, pk=pk)

    # Record analytics view
    viewer = request.user if request.user.is_authenticated else None
    ListingView.objects.create(listing_type="mess", listing_id=mess.id, viewer=viewer)

    # Get today's menu if it exists
    today_menu = mess.daily_menus.filter(date=date.today()).first()

    return render(
        request, "food/mess_detail.html", {"mess": mess, "today_menu": today_menu}
    )


@login_required
def update_daily_menu(request, mess_id):
    """
    Allows a Mess Owner to proactively update their Breakfast, Lunch, and Dinner items for the current day.
    This creates or updates a `DailyMenu` record tied to today's date so students can see fresh options.
    """
    # Ensure the user actually owns this mess (security check)
    mess = get_object_or_404(Mess, pk=mess_id, owner=request.user)
    today = date.today()
    menu, created = DailyMenu.objects.get_or_create(mess=mess, date=today)

    if request.method == "POST":
        menu.breakfast_items = request.POST.get("breakfast", "")
        menu.lunch_items = request.POST.get("lunch", "")
        menu.dinner_items = request.POST.get("dinner", "")
        menu.save()
        messages.success(request, f"Today's menu updated successfully for {mess.name}!")
        return redirect("mess_detail", pk=mess.id)

    return render(request, "food/menu_update_form.html", {"mess": mess, "menu": menu})


@login_required
def add_mess(request):
    """Allows owners to create and list a new Mess."""
    if request.user.role != "owner":
        messages.error(request, "Only owners can add Messes.")
        return redirect("home")

    if request.method == "POST":
        form = MessForm(request.POST, request.FILES)
        if form.is_valid():
            mess = form.save(commit=False)
            mess.owner = request.user
            mess.save()
            messages.success(request, f"Successfully added {mess.name}!")
            return redirect("owner_dashboard")
    else:
        form = MessForm()

    return render(request, "food/add_mess.html", {"form": form})


@login_required
def edit_mess(request, pk):
    """Allows owners to update details of an existing Mess they own."""
    mess = get_object_or_404(Mess, pk=pk)

    if request.user != mess.owner:
        messages.error(request, "You do not have permission to edit this Mess.")
        return redirect("owner_dashboard")

    if request.method == "POST":
        form = MessForm(request.POST, request.FILES, instance=mess)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated {mess.name}!")
            return redirect("owner_dashboard")
    else:
        form = MessForm(instance=mess)

    return render(request, "food/edit_mess.html", {"form": form, "mess": mess})

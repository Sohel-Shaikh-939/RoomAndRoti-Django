"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render


from housing.models import PG
from food.models import Mess
from users.models import StudentProfile


def home_view(request):
    """
    Renders the main homepage.
    If a Student is logged in, it runs a 'Smart Match' recommendation algorithm
    to suggest the top 3 PGs and Messes based on their saved StudentProfile preferences.
    """
    recommended_pgs = []
    recommended_messes = []

    if request.user.is_authenticated and request.user.role == "student":
        try:
            profile = request.user.student_profile
            all_pgs = PG.objects.all()
            all_messes = Mess.objects.all()

            # --- Score PGs ---
            # We assign arbitrary points for each matching amenity/price rule.
            # Higher score = Better match.
            scored_pgs = []
            for pg in all_pgs:
                score = 0
                if profile.target_budget and pg.starting_price <= profile.target_budget:
                    score += 3
                if profile.requires_ac and pg.has_ac:
                    score += 2
                if profile.requires_wifi and pg.has_wifi:
                    score += 2
                scored_pgs.append((score, pg))

            # --- Score Messes ---
            # We assign higher severity points (4) for strict dietary matches
            # since food restrictions (like Jain) are usually non-negotiable compared to WiFi.
            scored_messes = []
            for mess in all_messes:
                score = 0
                if profile.target_budget and mess.monthly_fee <= (
                    profile.target_budget * 0.4
                ):  # Assuming 40% of budget for food
                    score += 3
                if profile.preferred_food == "veg" and mess.is_veg_only:
                    score += 4
                elif profile.preferred_food == "jain" and mess.has_jain_food:
                    score += 4
                elif profile.preferred_food == "nonveg" and mess.has_non_veg:
                    score += 4
                scored_messes.append((score, mess))

            # Sort descending by score and take top 3
            scored_pgs.sort(key=lambda x: x[0], reverse=True)
            scored_messes.sort(key=lambda x: x[0], reverse=True)

            recommended_pgs = [pg for score, pg in scored_pgs[:3] if score > 0]
            recommended_messes = [
                mess for score, mess in scored_messes[:3] if score > 0
            ]

        except StudentProfile.DoesNotExist:
            pass

    return render(
        request,
        "home.html",
        {"recommended_pgs": recommended_pgs, "recommended_messes": recommended_messes},
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("pgs/", include("housing.urls")),
    path("messes/", include("food.urls")),
    path("", home_view, name="home"),
]

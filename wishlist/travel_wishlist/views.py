from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Place
from .forms import NewPlaceForm, TripReviewForm


# Create your views here.
@login_required(login_url="/admin/")
def place_list(request):
    if request.method == "POST":
        form = NewPlaceForm(request.POST)  # receiving data from a page
        place = form.save(commit=False)
        print(request.user for _ in range(10))
        place.user = request.user
        if form.is_valid():  # checking if entered data is not violating our constraints
            place.save()  # saving data in database
            return redirect("place_list")  # redirecting user to @place_list

    # Rendering places which are not visited
    places = Place.objects.filter(user=request.user).filter(visited=False).order_by("name")
    new_place_form = NewPlaceForm()
    return render(request, "travel_wishlist/wishlist.html", {"places": places, "new_place_form": new_place_form})


@login_required(login_url="/admin/")
def places_visited(request):
    # rendering places which are visited
    visited = Place.objects.filter(user=request.user).filter(visited=True)
    context = {"visited": visited}
    return render(request, "travel_wishlist/visited.html", context=context)


@login_required(login_url="/admin/")
def place_was_visited(request, place_pk):
    # Marking a unvisited place as visited
    if request.method == "POST":
        place = get_object_or_404(Place, pk=place_pk)
        print(place.user, request.user)
        if request.user == place.user:
            place.visited = True
            place.save()
        else:
            HttpResponseForbidden()
    return redirect("place_list")


@login_required(login_url="/admin/")
def place_details(request, place_pk):
    # getting details of places
    place = get_object_or_404(Place, pk=place_pk)

    if place.user != request.user:  # If place is deleted by some different user
        return HttpResponseForbidden()
    if request.method == "POST":
        form = TripReviewForm(request.POST, request.FILES, instance=place)

        if form.is_valid():
            form.save()
            messages.info(request, "Trip information update :)")
        else:
            messages.error(request, form.errors)
        return redirect("place_details", place_pk=place_pk)
    else:
        if place.visited:
            review_form = TripReviewForm(instance=place)
            return render(request, "travel_wishlist/place_details.html", {"place": place, "review_form": review_form})
        else:
            return render(request, "travel_wishlist/place_details.html", {"place": place})


@login_required(login_url="/admin/")
def delete_place(request, place_pk):
    # deleting a place
    place = get_object_or_404(Place, pk=place_pk)
    if place.user == request.user:
        place.delete()
        return redirect("place_list")
    else:
        return HttpResponseForbidden()

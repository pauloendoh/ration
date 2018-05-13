from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from core.forms import SignUpForm, ItemForm, UserItemForm, ProfileForm
from core.models import Item, User_Item, Profile
from core.utils import create_and_authenticate_user, get_logs_by_user, save_item_and_redirect, update_user_item, \
    get_latest_items, get_comparison_list


def home(request):
    latest_items = get_latest_items(10)
    return render(request, 'home.html', {'latest_items': latest_items})


def about(request):
    latest_items = get_latest_items(10)
    return render(request, 'about.html', {'latest_items': latest_items})


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    else:
        if not request.method == 'POST':
            form = SignUpForm()

        else:
            form = SignUpForm(request.POST)
            if form.is_valid():
                create_and_authenticate_user(request)
                return redirect('home')

        return render(request, 'signup.html', {'form': form})


def user(request, username):
    user = get_object_or_404(User, username=username)
    logs = get_logs_by_user(user)

    return render(request, 'user.html', {'user': user, 'logs': logs})


def user_item_list(request, username):
    user = get_object_or_404(User, username=username)
    user_item_list = User_Item.objects.filter(user=user)

    return render(request, 'user_items.html', {'user': user, 'user_item_list': user_item_list})


@login_required
def compare_items(request, username):
    your_user = request.user
    their_user = User.objects.get(username=username)

    comparison_list = get_comparison_list(your_user, their_user)

    return render(request, 'compare_items.html', {'their_user': their_user, 'comparison_list': comparison_list})


@login_required
def create_item(request):
    if not request.method == 'POST':
        form = ItemForm()
    else:
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            return save_item_and_redirect(request)

    return render(request, 'edit_item.html', {'form': form})


def item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if not request.user.is_authenticated:
        return render(request, 'item.html', {'item': item})

    else:
        user = request.user
        user_item = User_Item.objects.filter(user=user, item=item).first

        if not request.method == 'POST':
            form = UserItemForm()

        else:
            form = UserItemForm(request.POST)
            if form.is_valid():
                return update_user_item(user, item, form)

        return render(request, 'item.html', {'item': item, 'form': form, 'user_item': user_item})


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    user = request.user

    if not Item.objects.filter(creator=user, id=item_id).count() > 0:
        return redirect('item', item_id)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item.save()
            return redirect('item', item_id)
        else:
            return render(request, 'edit_item.html', {'item': item, 'form': form})
    else:
        return render(request, 'edit_item.html', {'item': item})


@login_required
def delete_item(request, item_id):
    user = request.user
    item = Item.objects.filter(id=item_id, creator=user)

    if item != None:
        item.delete()

    return redirect('home')


def items(request):
    items = Item.objects.all().order_by('-created_at')
    return render(request, 'items.html', {'items': items})


def search(request):
    query = request.GET.get('q')

    item_results = Item.objects.filter(Q(name__icontains=query) | Q(tag__icontains=query) | Q(description__icontains=query))

    user_results = User.objects.filter(Q(username__icontains=query) | Q(profile__fullname__icontains=query))

    return render(request, 'search.html', {'item_results': item_results, 'user_results': user_results})


@login_required
def settings(request):
    user = request.user

    if not request.method == 'POST':
        form = ProfileForm()
    else:
        # TODO try catch?
        if Profile.objects.filter(user=user).count() > 0:
            profile = Profile.objects.get(user=user)
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                profile.save()
                return redirect('user', user.username)
        else:
            form = ProfileForm(request.POST, request.FILES)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.user = user
                profile.save()
                return redirect('user', user.username)

    return render(request, 'settings.html', {'form': form})

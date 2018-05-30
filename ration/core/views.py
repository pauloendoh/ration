from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from core.forms import SignUpForm, ItemForm, UserItemForm, ProfileForm
from core.models import Item, User_Item, Profile, Tag, Following, Update, User_Tag, Favorite_User_Tag
from core.utils import create_and_authenticate_user, update_user_item, \
    get_latest_items, get_comparison_list, get_tag, \
    get_follower_list_by_user, get_latest_users, update_user_tag, get_arranged_ratings


def home(request):
    latest_items = get_latest_items(5)
    newest_users = get_latest_users(5)

    if request.user.is_authenticated:
        user = request.user

        following_list = Following.objects.filter(follower=user)

        update_list = []

        for following in following_list:
            # TODO
            user_tag = following.user_tag
            updates = user_tag.get_update_list()
            for update in updates:
                update_list.append(update)

        updates = Update.objects.filter(user=user)
        for update in updates:
            update_list.append(update)

        update_list.sort(key=lambda x: x.timestamp, reverse=True)

        return render(request, 'home.html',
                      {'latest_items': latest_items, 'update_list': update_list, 'newest_users': newest_users, })

    return render(request, 'home.html', {'latest_items': latest_items, 'newest_users': newest_users, })


def about(request):
    latest_items = get_latest_items(5)
    return render(request, 'about.html', {'latest_items': latest_items})


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    else:
        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                create_and_authenticate_user(request)
                return redirect('home')
        else:
            form = SignUpForm()

        return render(request, 'signup.html', {'form': form})


def user(request, username):
    user = get_object_or_404(User, username=username)

    # TODO: fix the update model (user, item, rating, ...?)
    update_list_query_set = Update.objects.filter(user=user)
    update_list = []

    if request.GET.get('tag'):
        tag_name = request.GET.get('tag')
        tag = get_object_or_404(Tag, name=tag_name)

        for update in update_list_query_set:
            try:
                if update.interaction.has_tag(tag):
                    update_list.append(update)
            except:
                pass
    else:
        for update in update_list_query_set:
            if update.interaction:
                update_list.append(update)

    update_list.sort(key=lambda x: x.timestamp, reverse=True)

    latest_items = get_latest_items(5)

    return render(request, 'home.html', {'user': user, 'update_list': update_list, 'latest_items': latest_items})


def users(request):
    user = request.user
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users, 'user': user})


def user_created_item_list(request, username):
    user = get_object_or_404(User, username=username)

    item_list = Item.objects.filter(creator=user)

    return render(request, 'user_created_item_list.html', {'item_list': item_list, 'user': user, })


def item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    latest_items = get_latest_items(5)

    if request.user.is_authenticated:
        user = request.user
        user_item = User_Item.objects.filter(user=user, item=item).first

        if request.method == 'POST':
            form = UserItemForm(request.POST)
            if form.is_valid():
                return update_user_item(user, item, form)

        else:
            form = UserItemForm()

        return render(request, 'item.html',
                      {'item': item, 'form': form, 'user_item': user_item, 'latest_items': latest_items})

    else:
        return render(request, 'item.html', {'item': item})


def items(request):
    if request.GET.get('tag'):
        tag_name = request.GET.get('tag')
        tag = get_object_or_404(Tag, name=tag_name)
        items = tag.items.all().order_by('-avg_rating')
    else:
        items = Item.objects.all().order_by('-avg_rating')
    return render(request, 'items.html', {'items': items})


def rating_list(request, username):
    user = get_object_or_404(User, username=username)

    ratings = []

    ratings_queryset = User_Item.objects.filter(user=user)

    is_following = False
    is_favorite = False
    user_tag = False

    if request.GET.get('tag'):
        tag_name = request.GET.get('tag')
        tag = get_object_or_404(Tag, name=tag_name)
        user_tag = User_Tag.objects.get(user=user, tag=tag)

        if user_tag.is_private and user_tag.user != request.user:
            return redirect('home')

        if Favorite_User_Tag.objects.filter(user=request.user, user_tag=user_tag).count() > 0:
            is_favorite = True

        if Following.objects.filter(follower=request.user, user_tag=user_tag).count() > 0:
            is_following = True

        for user_item in ratings_queryset:
            if user_item.has_tag(tag):
                ratings.append(user_item)
    else:
        for user_item in ratings_queryset:
            ratings.append(user_item)

    order = request.GET.get('order', 'name')
    sort = request.GET.get('sort', 'asc')

    ratings = get_arranged_ratings(ratings, order, sort)

    return render(request, 'ratings.html',
                  {'user': user, 'rating_list': ratings, 'user_tag': user_tag, 'is_following': is_following,
                   'is_favorite': is_favorite, })


@login_required
def create_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user

            item = form.save(commit=False)
            item.creator = user
            item.save()

            raw_tags = request.POST.get('tags').split(';')
            for raw_tag in raw_tags:
                if raw_tag != "" and raw_tag != " ":
                    tag_name = raw_tag.lower().strip()
                    tag = get_tag(tag_name)
                    item.tags.add(tag)

            message = "New item: " + item.name
            Update.objects.create(user=user, message=message)

            return redirect('item', item.id)
    else:
        form = ItemForm()
    return render(request, 'edit_item.html', {'form': form})


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    user = request.user

    if Item.objects.filter(creator=user, id=item_id).count() == 0:
        return redirect('item', item_id)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item.save()

            item.tags.clear()
            raw_tags = form.cleaned_data['tags'].split(';')
            for raw_tag in raw_tags:
                if raw_tag != "" and raw_tag != " ":
                    tag = get_tag(raw_tag.lower().strip())
                    item.tags.add(tag)

            message = "Edited an item: " + item.name
            Update.objects.create(user=user, message=message)

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


@login_required
def compare_items(request, username):
    your_user = request.user
    their_user = User.objects.get(username=username)

    comparison_list = get_comparison_list(your_user, their_user)

    return render(request, 'compare_items.html', {'their_user': their_user, 'comparison_list': comparison_list})


def search(request):
    query = request.GET.get('q')

    item_results = Item.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query))

    user_results = User.objects.filter(Q(username__icontains=query) | Q(profile__fullname__icontains=query))

    tag_results = Tag.objects.filter(name__icontains=query)
    if query.startswith('#'):
        tag_name = query.split('#')[1].strip()
        tag_results = Tag.objects.filter(name__icontains=tag_name)

    return render(request, 'search.html', {'item_results': item_results, 'user_results': user_results, 'tag_results': tag_results})


@login_required
def settings(request):
    user = request.user
    latest_items = get_latest_items(5)

    if request.method == 'POST':
        try:
            profile = Profile.objects.get(user=user)
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                profile.save()
                return redirect('user', user.username)
        except:
            form = ProfileForm(request.POST, request.FILES)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.user = user
                profile.save()
                return redirect('user', user.username)
    else:
        form = ProfileForm()
    return render(request, 'settings.html', {'form': form, 'latest_items': latest_items})


@login_required
def follow(request, user_tag_id):
    user = request.user

    user_tag = get_object_or_404(User_Tag, id=user_tag_id)

    if Following.objects.filter(follower=user, user_tag=user_tag).count() > 0:
        Following.objects.filter(follower=user, user_tag=user_tag).delete()
    else:
        Following.objects.create(follower=user, user_tag=user_tag)

    return redirect(reverse('rating_list', kwargs={'username': user_tag.user.username}) + '?tag=' + user_tag.tag.name)


def following_list(request, username):
    user = get_object_or_404(User, username=username)

    following_list = Following.objects.filter(follower=user)

    return render(request, 'following.html', {'following_list': following_list, 'user': user})


def follower_list(request, username):
    user = get_object_or_404(User, username=username)

    follower_list = get_follower_list_by_user(user)

    return render(request, 'followers.html', {'user': user, 'follower_list': follower_list})


@login_required
def update_interaction(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        item_id = request.POST.get('item_id')

        user = User.objects.get(id=user_id)
        item = Item.objects.get(id=item_id)

        rating = request.POST.get('rating')
        interest = request.POST.get('interest')

        form = UserItemForm(request.POST)
        if form.is_valid():
            user_item = form.save(commit=False)
            user_item.user = user
            user_item.item = item

            if User_Item.objects.filter(user=request.user, item=item).count() > 0:
                user_item = User_Item.objects.filter(user=request.user, item=item).first()

                if user_item.rating == int(rating) and user_item.interest == int(interest):
                    data = {
                        'message' : 'Score or interest must be different!'
                    }
                    return JsonResponse(data)

                user_item.rating = rating
                user_item.interest = interest
            user_item.save()
            user_item.item.calc_average()

            updates = Update.objects.filter(interaction=user_item)
            for update in updates:
                update.is_visible = False
                update.save()

            message = "updated their rating (Score: " + str(user_item.rating) + \
                      "; Interest: " + str(user_item.interest) + ")"
            Update.objects.create(user=user, message=message, interaction=user_item, is_visible=True)

            for tag in item.tags.all():
                update_user_tag(user, tag)

            data = {
                'message': 'Saved!'
            }

            return JsonResponse(data)


@login_required
def private_user_tag(request, user_tag_id):
    user = request.user
    user_tag = User_Tag.objects.get(id=user_tag_id)
    if user_tag.user == user:
        if user_tag.is_private:
            user_tag.is_private = False
        else:
            user_tag.is_private = True
        user_tag.save()
    return redirect(reverse('rating_list', kwargs={'username': user.username}) + '?tag=' + user_tag.tag.name)


@login_required
def favorite_user_tag(request, user_tag_id):
    user = request.user
    user_tag = User_Tag.objects.get(id=user_tag_id)

    try:
        Favorite_User_Tag.objects.get(user=user, user_tag=user_tag).delete()
    except:
        Favorite_User_Tag.objects.create(user=user, user_tag=user_tag)

    return redirect(reverse('rating_list', kwargs={'username': user.username}) + '?tag=' + user_tag.tag.name)


@login_required
def hide_update(request, update_id):
    update = get_object_or_404(Update, id=update_id)

    if update.user == request.user:
        update.is_visible = False
        update.save()

    return redirect('user', update.user.username)

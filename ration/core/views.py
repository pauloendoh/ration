from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from core.forms import SignUpForm, ItemForm, UserItemForm, ProfileForm, UpdateScoreForm, UpdateInterestForm
from core.models import Item, User_Item, Profile, Tag, Following, Update, User_Tag, Favorite_User_Tag, Notification
from core.utils import update_user_item, \
    get_latest_items, get_comparison_list, get_or_create_tag, \
    get_latest_users, update_user_tag, get_arranged_ratings, get_ratings, get_comparisons


def home(request):
    latest_items = get_latest_items(5)
    newest_users = get_latest_users(5)

    if request.user.is_authenticated:
        user = request.user
        updates = user.get_all_updates()

        return render(request, 'home.html', {'latest_items': latest_items,
                                             'updates': updates,
                                             'newest_users': newest_users, })

    return render(request, 'home.html', {'latest_items': latest_items,
                                         'newest_users': newest_users, })


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
                form.save()
                form.login(request)
                return redirect('home')
        else:
            form = SignUpForm()

        return render(request, 'signup.html', {'form': form})


def user(request, username):
    user = get_object_or_404(User, username=username)

    tag_name = request.GET.get('tag', '')
    updates = user.get_updates_by_tag_name(tag_name)

    updates.sort(key=lambda x: x.timestamp, reverse=True)

    latest_items = get_latest_items(5)

    return render(request, 'home.html', {'user': user,
                                         'updates': updates,
                                         'latest_items': latest_items})


def users(request):
    user = request.user
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users,
                                              'user': user})


def user_created_item_list(request, username):
    user = get_object_or_404(User, username=username)

    item_list = Item.objects.filter(creator=user)

    return render(request, 'user_created_item_list.html', {'item_list': item_list,
                                                           'user': user, })


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

        return render(request, 'item.html', {'item': item,
                                             'form': form,
                                             'user_item': user_item,
                                             'latest_items': latest_items})

    else:
        return render(request, 'item.html', {'item': item,
                                             'latest_items': latest_items})


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

    tag_name = request.GET.get('tag', '')
    order = request.GET.get('order', 'score')
    sort = request.GET.get('sort', 'desc')

    if request.user.is_authenticated and request.user != user:
        comparisons = get_comparisons(user, request.user, tag_name, order, sort)
        return render(request, 'ratings.html', {'user': user,
                                                'comparisons': comparisons})
    else:
        ratings = get_ratings(user, tag_name, order, sort)
        return render(request, 'ratings.html', {'user': user,
                                                'rating_list': ratings,
                                                })


@login_required
def create_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            if request.POST.get('is_official') == 'on':
                is_official = True
            else:
                is_official = False

            item = form.save(commit=False)
            item.creator = user
            item.is_official = is_official
            item.save()

            raw_tags = request.POST.get('tags').split(';')
            for raw_tag in raw_tags:
                if raw_tag != "" and raw_tag != " ":
                    tag_name = raw_tag.lower().strip()
                    tag = get_or_create_tag(tag_name)
                    item.tags.add(tag)

            message = "created: "
            user_item = user.get_or_create_user_item(item)
            Update.objects.create(user=user,
                                  message=message,
                                  is_visible=True,
                                  interaction=user_item)

            return redirect('item', item.id)
        else:
            return render(request, 'edit_item.html', {'form': form})
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
            if request.POST.get('is_official') == 'on':
                is_official = True
            else:
                is_official = False
            item.is_official = is_official
            item.save()

            item.tags.clear()
            raw_tags = form.cleaned_data['tags'].split(';')
            for raw_tag in raw_tags:
                if raw_tag != "" and raw_tag != " ":
                    tag = get_or_create_tag(raw_tag.lower().strip())
                    item.tags.add(tag)

            message = "edited an item: "
            user_item = user.get_or_create_user_item(item)

            user.hide_all_updates_by_user_item(user_item)

            Update.objects.create(user=user,
                                  message=message,
                                  is_visible=True,
                                  interaction=user_item)

            return redirect('item', item_id)
        else:
            return render(request, 'edit_item.html', {'item': item,
                                                      'form': form})
    else:
        return render(request, 'edit_item.html', {'item': item})


@login_required
def delete_item(request, item_id):
    user = request.user
    item = Item.objects.get(id=item_id, creator=user)

    for tag in item.tags.all():

        if tag.item_count() == 1:
            tag.delete()

    item.delete()

    return redirect('home')


@login_required
def compare_items(request, username):
    your_user = request.user
    their_user = User.objects.get(username=username)

    comparison_list = get_comparison_list(your_user, their_user)

    return render(request, 'compare_items.html', {'their_user': their_user,
                                                  'comparison_list': comparison_list})


def search(request):
    query = request.GET.get('q')

    item_results = Item.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query))

    user_results = User.objects.filter(Q(username__icontains=query) | Q(profile__fullname__icontains=query))

    tag_results = Tag.objects.filter(name__icontains=query)
    if query.startswith('#'):
        tag_name = query.split('#')[1].strip()
        tag_results = Tag.objects.filter(name__icontains=tag_name)

    return render(request, 'search.html', {'item_results': item_results,
                                           'user_results': user_results,
                                           'tag_results': tag_results})


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
    return render(request, 'settings.html', {'form': form,
                                             'latest_items': latest_items})


@login_required
def follow(request):
    if request.POST:
        user_tag_id = request.POST.get('user_tag_id')
        user_tag = get_object_or_404(User_Tag, id=user_tag_id)

        if Following.objects.filter(follower=request.user, user_tag=user_tag).count() > 0:
            Following.objects.filter(follower=request.user, user_tag=user_tag).delete()
            data = {
                'message': 'Follow'
            }
        else:
            Following.objects.create(follower=request.user, user_tag=user_tag)

            message = "@" + request.user.username + " is following your '" + user_tag.tag.name + "' user tag!"
            Notification.objects.create(user=user_tag.user, message=message, is_new=True, was_new=False)
            data = {
                'message': 'Unfollow'
            }

        return JsonResponse(data)


def following_list(request, username):
    user = get_object_or_404(User, username=username)

    following_queryset = Following.objects.filter(follower=user)
    followings = []

    for fq in following_queryset:
        already_following = False

        for f in followings:
            if f.user_tag.user.id == fq.user_tag.user.id:
                already_following = True
        if already_following == False:
            followings.append(fq)

    return render(request, 'following.html', {'followings': followings,
                                              'user': user})


def follower_list(request, username):
    user = get_object_or_404(User, username=username)

    follower_list = user.get_followers()

    return render(request, 'followers.html', {'user': user,
                                              'follower_list': follower_list})


@login_required
def update_score(request):
    user_id = request.POST.get('user_id')
    item_id = request.POST.get('item_id')

    user = User.objects.get(id=user_id)
    item = Item.objects.get(id=item_id)

    score = int(request.POST.get('score'))

    form = UpdateScoreForm(request.POST)
    if form.is_valid():
        user_item = form.save(commit=False)
        user_item.user = user
        user_item.item = item

        if User_Item.objects.filter(user=user, item=item).count() > 0:
            user_item = User_Item.objects.get(user=user, item=item)

            if user_item.rating != None and int(user_item.rating) == int(score):
                user_item.rating = None
                user_item.save()

                if user_item.rating == None and user_item.interest == None:
                    user_item.delete()

                data = {
                    'message': 'Score deleted.'
                }
                return JsonResponse(data)

        user_item.rating = score
        user_item.save()
        user_item.item.calc_average()

        user.hide_all_updates_by_user_item(user_item)

        message = "scored "

        for x in range(1, 6):
            if int(user_item.rating) >= x:
                message = message + "★"
            else:
                message = message + "✰"

        message = message + ":"

        Update.objects.create(user=user,
                              message=message,
                              interaction=user_item,
                              is_visible=True)

        for tag in item.tags.all():
            update_user_tag(user, tag)

        data = {
            'message': 'You ' + message + ' (' + item.name + ')'
        }
        return JsonResponse(data)


@login_required
def update_interest(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        item_id = request.POST.get('item_id')

        user = User.objects.get(id=user_id)
        item = Item.objects.get(id=item_id)

        interest = request.POST.get('interest')

        form = UpdateInterestForm(request.POST)
        if form.is_valid():
            user_item = form.save(commit=False)
            user_item.user = user
            user_item.item = item

            if User_Item.objects.filter(user=user, item=item).count() > 0:
                user_item = User_Item.objects.get(user=user, item=item)

                if int(user_item.interest) == int(interest):
                    user_item.interest = None
                    user_item.save()
                    if user_item.rating == None and user_item.interest == None:
                        user_item.delete()
                    data = {
                        'message': 'You removed an interest.'
                    }
                    return JsonResponse(data)

                user_item.interest = interest

            user_item.save()
            user_item.item.calc_average()

            user.hide_all_updates_by_user_item(user_item)

            message = Update.generate_message_by_interest(int(interest))

            Update.objects.create(user=user,
                                  message=message,
                                  interaction=user_item,
                                  is_visible=True)

            for tag in item.tags.all():
                update_user_tag(user, tag)

            data = {
                'message': "You're " + message + " " + item.name
            }
            return JsonResponse(data)


@login_required
def recommend_item(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        user_id = request.POST.get('user_id')

        item = Item.objects.get(id=item_id)
        user = User.objects.get(id=user_id)

        message = '@' + request.user.username + " recommended you: '" + item.name + "'"
        Notification.objects.create(user=user, message=message)

        data = {
            'message': 'You recommended @' + user.username + ' an item!'
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
def favorite_user_tag(request):
    if request.POST:
        user_tag_id = request.POST.get('user_tag_id')
        user_tag = get_object_or_404(User_Tag, id=user_tag_id)

        if Favorite_User_Tag.objects.filter(user=request.user, user_tag=user_tag).count() > 0:
            Favorite_User_Tag.objects.filter(user=request.user, user_tag=user_tag).delete()
            data = {
                'message': 'Favorite'
            }
        else:
            Favorite_User_Tag.objects.create(user=request.user, user_tag=user_tag)

            data = {
                'message': 'Unfavorite'
            }

        return JsonResponse(data)


@login_required
def hide_update(request, update_id):
    update = get_object_or_404(Update, id=update_id)

    if update.user == request.user:
        update.is_visible = False
        update.save()

    return redirect('user', update.user.username)


def get_search_results(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        results = []

        items = Item.objects.filter(name__icontains=q)
        users = User.objects.filter(username__icontains=q)
        tags = Tag.objects.filter(name__icontains=q)

        for item in items:
            item_json = {}
            item_json['id'] = item.id
            item_json['label'] = item.name
            item_json['value'] = "item/" + str(item.id)
            results.append(item_json)

        for user in users:
            user_json = {}
            user_json['id'] = user.id
            user_json['label'] = "@" + user.username
            user_json['value'] = "user/" + user.username
            results.append(user_json)

        for tag in tags:
            tag_json = {}
            tag_json['id'] = tag.id
            tag_json['label'] = "#" + tag.name
            tag_json['value'] = "items?tag=" + tag.name
            results.append(tag_json)

        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    for notification in notifications:
        if notification.was_new:
            notification.was_new = False
            notification.save()
        if notification.is_new:
            notification.is_new = False
            notification.was_new = True
            notification.save()

    return render(request, 'notifications.html', {'notifications': notifications, })


@login_required
def update_following(request):
    list = request.POST.getlist('list[]', [])

    for x in list:
        y = json.loads(x)
        user_tag_id = y['user_tag_id']

        user_tag = User_Tag.objects.get(id=user_tag_id)

        if y['is_following'] == True:
            if request.user.is_following(user_tag) == False:
                Following.objects.create(follower=request.user, user_tag=user_tag)
                message = "@" + request.user.username + " is following your '" + user_tag.tag.name + "' user tag!"
                Notification.objects.create(user=user_tag.user, message=message, is_new=True, was_new=False)

        else:
            if request.user.is_following(user_tag) == True:
                Following.objects.get(follower=request.user, user_tag=user_tag).delete()

    data = {
        'message': 'Success!'
    }
    return JsonResponse(data)

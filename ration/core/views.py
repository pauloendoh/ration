from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from core.forms import SignUpForm, ItemForm, UserItemForm, ProfileForm, TaglistForm
from core.models import Item, User_Item, Profile, Taglist, Tag, Following, Update
from core.utils import create_and_authenticate_user, get_logs_by_user, update_user_item, \
    get_latest_items, get_comparison_list, get_tag, generate_taglist_logs, \
    get_follower_list_by_user, get_latest_users


def home(request):
    latest_items = get_latest_items(5)
    newest_users = get_latest_users(5)

    if request.user.is_authenticated:
        user = request.user

        following_list = Following.objects.filter(follower=user)

        log_list = []

        update_list = []

        for following in following_list:
            taglist = following.taglist
            updates = taglist.get_update_list()
            for update in updates:
                update_list.append(update)

        update_list.sort(key=lambda x: x.timestamp, reverse=True)

        for following in following_list:
            taglist = following.taglist
            for log in taglist.logs.all():
                log_list.append(log)

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

    latest_items = get_latest_items(5)

    taglist = Taglist.objects.filter(user=user).first()
    taglists = Taglist.objects.filter(user=user)
    for tl in taglists:
        if tl.is_main:
            taglist = tl

    update_list = taglist.get_update_list()

    return render(request, 'user.html',
                  {'user': user, 'latest_items': latest_items, 'update_list': update_list, 'taglist': taglist})


def user_list(request):
    user = request.user
    user_list = User.objects.all()
    return render(request, 'user_list.html', {'user_list': user_list, 'user': user})


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
    user_item_query_set = User_Item.objects.filter(user=user)

    rating_list = []

    if request.GET.get('tag'):
        tag_name = request.GET.get('tag')
        tag = get_object_or_404(Tag, name=tag_name)
        for user_item in user_item_query_set:
            if user_item.has_tag(tag):
                rating_list.append(user_item)
    else:
        for user_item in user_item_query_set:
            rating_list.append(user_item)

    order = request.GET.get('order', 'name')
    sort = request.GET.get('sort', 'asc')
    if order == 'name':
        if sort == 'asc':
            rating_list.sort(key=lambda x: x.item.name)
        else:
            rating_list.sort(key=lambda x: x.item.name, reverse=True)
    if order == 'ration':
        if sort == 'asc':
            rating_list = sorted(rating_list, key=lambda x: (x.item.avg_rating is None, x.item.avg_rating))
        else:
            rating_list = sorted(rating_list, reverse=True,
                                 key=lambda x: (x.item.avg_rating is not None, x.item.avg_rating))
    if order == 'score':
        if sort == 'asc':
            rating_list = sorted(rating_list, key=lambda x: (x.rating is None, x.rating))
        else:
            rating_list = sorted(rating_list, reverse=True, key=lambda x: (x.rating is not None, x.rating))
    if order == 'interest':
        if sort == 'asc':
            rating_list = sorted(rating_list, key=lambda x: (x.interest is None, x.interest))
        else:
            rating_list = sorted(rating_list, reverse=True, key=lambda x: (x.interest is not None, x.interest))

    return render(request, 'ratings.html', {'user': user, 'rating_list': rating_list})


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
                    generate_taglist_logs(user, item, tag_name)

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

    return render(request, 'search.html', {'item_results': item_results, 'user_results': user_results})


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
def create_taglist(request):
    if request.method == 'POST':
        form = TaglistForm(request.POST)
        if form.is_valid():
            taglist = form.save(commit=False)
            taglist.user = request.user

            if taglist.is_main:
                taglists = Taglist.objects.filter(user=taglist.user)
                for x in taglists:
                    if x.is_main:
                        x.is_main = False
                        x.save()

            taglist.save()

            raw_tags = form.cleaned_data['tags'].split(';')
            for raw_tag in raw_tags:
                if raw_tag != "" and raw_tag != " ":
                    tag_name = raw_tag.lower().strip()
                    tag = get_tag(tag_name)
                    taglist.tags.add(tag)

            return redirect('taglist', taglist.id)
    else:
        form = TaglistForm()
    return render(request, 'edit_taglist.html', {'form': form})


@login_required
def edit_taglist(request, taglist_id):
    user = request.user
    taglist = get_object_or_404(Taglist, id=taglist_id)

    if Taglist.objects.filter(user=user, id=taglist_id).count() == 0:
        return redirect('taglist', taglist_id)

    if request.method == 'POST':
        form = TaglistForm(request.POST, instance=taglist)
        if form.is_valid():

            if taglist.is_main:
                taglists = Taglist.objects.filter(user=taglist.user)
                for x in taglists:
                    if x.is_main:
                        x.is_main = False
                        x.save()

            taglist.save()

            taglist.tags.clear()
            raw_tags = form.cleaned_data['tags'].split(';')
            for raw_tag in raw_tags:
                if raw_tag != "" and raw_tag != " ":
                    tag = get_tag(raw_tag.lower().strip())
                    taglist.tags.add(tag)

            return redirect('taglist', taglist_id)
        else:
            return render(request, 'edit_item.html', {'item': item, 'form': form})
    else:
        return render(request, 'edit_taglist.html', {'taglist': taglist})


def taglist(request, taglist_id):
    taglist = get_object_or_404(Taglist, id=taglist_id)
    user = request.user

    taglist_update_list = taglist.get_update_list()

    taglist_update_list.sort(key=lambda x: x.timestamp, reverse=True)

    if request.user.is_authenticated:
        if Following.objects.filter(follower=user, taglist=taglist).count() > 0:
            return render(request, 'taglist.html', {'taglist': taglist, 'is_following': True, 'user': taglist.user,
                                                    'taglist_update_list': taglist_update_list})

    return render(request, 'taglist.html',
                  {'taglist': taglist, 'user': taglist.user, 'taglist_update_list': taglist_update_list})


@login_required
def delete_taglist(request, taglist_id):
    user = request.user
    taglist = get_object_or_404(Taglist, id=taglist_id)

    if user == taglist.user:
        taglist.delete()

    return redirect('home')


@login_required
def follow(request, taglist_id):
    user = request.user

    taglist = get_object_or_404(Taglist, id=taglist_id)

    if Following.objects.filter(follower=user, taglist=taglist).count() > 0:
        Following.objects.filter(follower=user, taglist=taglist).delete()
    else:
        Following.objects.create(follower=user, taglist=taglist)
    return redirect('taglist', taglist_id)


def following_list(request, username):
    user = get_object_or_404(User, username=username)

    following_list = Following.objects.filter(follower=request.user)

    return render(request, 'following.html', {'following_list': following_list, 'user': user})


def follower_list(request, username):
    user = get_object_or_404(User, username=username)

    follower_list = get_follower_list_by_user(user)

    return render(request, 'followers.html', {'user': user, 'follower_list': follower_list})


@login_required
def update_rating(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    user = request.user

    if request.method == 'POST':
        form = UserItemForm(request.POST)
        if form.is_valid():
            return update_user_item(user, item, form)
    else:
        return redirect('home')


@login_required
def update_interaction(request):
    data = {
        'teste': 'Testando123'
    }

    if request.method == 'POST':
        rating = request.POST.get('rating')
        interest = request.POST.get('interest')
        user_id = request.POST.get('user_id')
        item_id = request.POST.get('item_id')

        user = User.objects.get(id=user_id)

        item = Item.objects.get(id=item_id)

        form = UserItemForm(request.POST)
        if form.is_valid():
            user_item = form.save(commit=False)
            user_item.user = user
            user_item.item = item

            if User_Item.objects.filter(user=request.user, item=item).count() > 0:
                user_item = User_Item.objects.filter(user=request.user, item=item).first()
                user_item.rating = rating
                user_item.interest = interest
            user_item.save()
            user_item.item.calc_average()

            message = "Updated their rating (Score: " + str(user_item.rating) + \
                      "; Interest: " + str(user_item.interest) + ")"
            Update.objects.create(user=user, message=message, interaction=user_item)

            return JsonResponse(data)


def user_timeline(request, username):
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

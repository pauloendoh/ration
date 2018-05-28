from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect

from core.forms import SignUpForm
from core.models import User_Item, Item, Tag, Update, User_Tag, Following


def create_and_authenticate_user(request):
    form = SignUpForm(request.POST)
    form.save()

    username = form.cleaned_data.get('username')
    password = form.cleaned_data.get('password1')

    user = authenticate(username=username, password=password)
    auth_login(request, user)

    return


def get_tag(name):
    if Tag.objects.filter(name=name).count() > 0:
        tag = Tag.objects.filter(name=name).first()
        return tag
    else:
        tag = Tag.objects.create(name=name)
        return tag


def update_user_tag(user, tag):
    item_count = len(user.get_ratings_by_tag(tag))

    if User_Tag.objects.filter(user=user, tag=tag).count() == 0:
        User_Tag.objects.create(user=user, tag=tag, item_count=item_count, is_private=True)
    else:
        user_tag = User_Tag.objects.get(user=user, tag=tag)
        user_tag.item_count = item_count
        user_tag.save()


def update_all_user_tag():
    users = User.objects.all()

    for user in users:
        tag_list = user.get_tag_list()
        for tag in tag_list:
            item_count = len(user.get_ratings_by_tag(tag))

            if User_Tag.objects.filter(user=user, tag=tag).count() == 0:
                User_Tag.objects.create(user=user, tag=tag, item_count=item_count, is_private=True)
            else:
                user_tag = User_Tag.objects.get(user=user, tag=tag)
                user_tag.item_count = item_count
                user_tag.save()


def update_user_item(user, item, form):
    if User_Item.objects.filter(user=user, item=item).count() > 0:
        user_item = User_Item.objects.filter(user=user, item=item).first()
        user_item.rating = form.cleaned_data['rating']
        user_item.interest = form.cleaned_data['interest']
    else:
        user_item = form.save(commit=False)
        user_item.user = user
        user_item.item = item

    user_item.save()
    item.calc_average()

    message = "Updated an item's ratings: " + item.name + " ( Score: " + str(user_item.rating) + \
              " | Interest: " + str(user_item.interest) + " )"
    Update.objects.create(user=user, message=message, interaction=user_item)

    for tag in item.tags.all():
        update_user_tag(user, tag)

    return redirect('item', item.id)


def get_latest_items(n):
    item_list = Item.objects.all().order_by('-created_at')[:n]
    return item_list


def get_latest_users(n):
    users = User.objects.all().order_by('-id')[:n]
    return users


class Comparison:
    def __init__(self, user_item, your_user, their_user):
        self.item = user_item.item
        if User_Item.objects.filter(user=your_user, item=user_item.item).count() > 0:
            self.your_rating = User_Item.objects.filter(user=your_user, item=user_item.item).first().rating
            self.your_interest = User_Item.objects.filter(user=your_user, item=user_item.item).first().interest
        else:
            self.your_rating = None
            self.your_interest = None
        if User_Item.objects.filter(user=their_user, item=user_item.item).count() > 0:
            self.their_rating = User_Item.objects.filter(user=their_user, item=user_item.item).first().rating
            self.their_interest = User_Item.objects.filter(user=their_user, item=user_item.item).first().interest
        else:
            self.their_rating = None
            self.their_interest = None

    def equals(self, other):
        if self.item == other.item:
            if self.your_rating == other.your_rating:
                if self.your_interest == other.your_interest:
                    if self.their_rating == other.their_rating:
                        if self.their_interest == other.their_interest:
                            return 1
        return 0


def get_comparison_list(your_user, their_user):
    comparison_list = []

    rating_list = User_Item.objects.filter(Q(user=your_user) | Q(user=their_user))

    for user_item in rating_list:
        comparison = Comparison(user_item, your_user, their_user)
        comparison_exists = False

        for other in comparison_list:

            if comparison.equals(other):
                comparison_exists = True

        if not comparison_exists:
            comparison_list.append(comparison)

    return comparison_list


def get_follower_list_by_user(user):
    follower_list = []

    user_tags = User_Tag.objects.filter(user=user)

    for user_tag in user_tags:
        followings = Following.objects.filter(user_tag=user_tag)
        for following in followings:
            in_list = False

            for follower in follower_list:
                if follower.id == following.follower.id:
                    in_list = True
            if not in_list:
                follower_list.append(following.follower)

    return follower_list


def get_arranged_ratings(ratings, order, sort):
    if order == 'name':
        if sort == 'asc':
            ratings.sort(key=lambda x: x.item.name)
        else:
            ratings.sort(key=lambda x: x.item.name, reverse=True)
    if order == 'ration':
        if sort == 'asc':
            ratings = sorted(ratings, key=lambda x: (x.item.avg_rating is None, x.item.avg_rating))
        else:
            ratings = sorted(ratings, reverse=True,
                             key=lambda x: (x.item.avg_rating is not None, x.item.avg_rating))
    if order == 'score':
        if sort == 'asc':
            ratings = sorted(ratings, key=lambda x: (x.rating is None, x.rating))
        else:
            ratings = sorted(ratings, reverse=True, key=lambda x: (x.rating is not None, x.rating))
    if order == 'interest':
        if sort == 'asc':
            ratings = sorted(ratings, key=lambda x: (x.interest is None, x.interest))
        else:
            ratings = sorted(ratings, reverse=True, key=lambda x: (x.interest is not None, x.interest))

    return ratings


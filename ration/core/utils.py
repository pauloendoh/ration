from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404

from core.forms import SignUpForm
from core.models import User_Item, Tag, Update, User_Tag, Following, Item


def get_or_create_tag(name):
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


'''
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
'''


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


class Comparison:
    def __init__(self, user_item, user1, user2):
        self.item = user_item.item
        self.user1 = user1
        self.user2 = user2
        self.rating1 = user_item.rating
        self.interest1 = user_item.interest

        if User_Item.objects.filter(user=user2, item=user_item.item).count() > 0:
            user2_item = User_Item.objects.get(user=user2, item=user_item.item)
            self.rating2 = user2_item.rating
            self.interest2 = user2_item.interest
            if self.rating1 != None and self.rating2 != None:
                self.rating_difference = abs(self.rating1 - self.rating2)
                self.avg_rating = (self.rating1 + self.rating2) / 2
            else:
                self.rating_difference = None
                self.avg_rating = None
            if self.interest1 != None and self.interest2 != None:
                self.avg_interest = (self.interest1)
            else:
                self.avg_interest = None
        else:
            self.rating2 = None
            self.interest2 = None
            self.rating_difference = None
            self.avg_rating = None
            self.avg_interest = None


def get_comparisons(user1, user2, tag_name, order, sort):
    comparisons = []

    user_items = User_Item.objects.filter(user=user1)

    for user_item in user_items:
        if tag_name == '':
            comparison = Comparison(user_item, user1, user2)
            comparisons.append(comparison)
        else:
            tag = get_object_or_404(Tag, name=tag_name)
            if user_item.has_tag(tag):
                comparison = Comparison(user_item, user1, user2)
                comparisons.append(comparison)
    comparisons = arrange_comparisons(comparisons, order, sort)
    return comparisons

def arrange_comparisons(comparisons, order, sort):
    if order == 'name':
        if sort == 'asc':
            comparisons.sort(key=lambda x: x.item.name)
        else:
            comparisons.sort(key=lambda x: x.item.name, reverse=True)
    if order == 'score' or order == 'score1':
        if sort == 'asc':
            comparisons = sorted(comparisons, key=lambda x: (x.rating1 is None, x.rating1))
        else:
            comparisons = sorted(comparisons, reverse=True, key=lambda x: (x.rating1 is not None, x.rating1))
    if order == 'interest1':
        if sort == 'asc':
            comparisons = sorted(comparisons, key=lambda x: (x.interest1 is None, x.interest1))
        else:
            comparisons = sorted(comparisons, reverse=True, key=lambda x: (x.interest1 is not None, x.interest1))
    if order == 'score2':
        if sort == 'asc':
            comparisons = sorted(comparisons, key=lambda x: (x.rating2 is None, x.rating2))
        else:
            comparisons = sorted(comparisons, reverse=True, key=lambda x: (x.rating2 is not None, x.rating2))
    if order == 'interest2':
        if sort == 'asc':
            comparisons = sorted(comparisons, key=lambda x: (x.interest2 is None, x.interest2))
        else:
            comparisons = sorted(comparisons, reverse=True, key=lambda x: (x.interest2 is not None, x.interest2))
    if order == 'sco_diff':
        if sort == 'asc':
            comparisons = sorted(comparisons, key=lambda x: (x.rating_difference is None, x.rating_difference))
        else:
            comparisons = sorted(comparisons, reverse=True, key=lambda x: (x.rating_difference is not None, x.rating_difference))
    if order == 'avg_sco':
        if sort == 'asc':
            comparisons = sorted(comparisons, key=lambda x: (x.avg_rating is None, x.avg_rating))
        else:
            comparisons = sorted(comparisons, reverse=True, key=lambda x: (x.avg_rating is not None, x.avg_rating))
    if order == 'avg_int':
        if sort == 'asc':
            comparisons = sorted(comparisons, key=lambda x: (x.avg_interest is None, x.avg_interest))
        else:
            comparisons = sorted(comparisons, reverse=True, key=lambda x: (x.avg_interest is not None, x.avg_interest))

    return comparisons

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


def get_ratings(user, tag_name, order, sort):
    ratings = []
    ratings_queryset = User_Item.objects.filter(user=user)

    if tag_name == '':

        for rating in ratings_queryset:
            ratings.append(rating)
    else:
        tag = get_object_or_404(Tag, name=tag_name)
        for rating in ratings_queryset:
            if rating.has_tag(tag):
                ratings.append(rating)
    ratings = get_arranged_ratings(ratings, order, sort)
    return ratings

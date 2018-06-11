from django import template
from django.shortcuts import get_object_or_404

from core.models import User_Item, Following, Item, Update, User_Tag, Tag

register = template.Library()


@register.simple_tag
def get_user_score_by_item(user, item):
    try:
        user_item = User_Item.objects.filter(user=user, item=item).first()
        return int(user_item.rating)
    except:
        pass


@register.simple_tag
def get_user_interest_by_item(user, item):
    try:
        user_item = User_Item.objects.filter(user=user, item=item).first()
        return int(user_item.interest)
    except:
        pass


@register.simple_tag
def get_follower_count_by_user(user):
    followers = user.get_followers()
    return len(followers)


@register.simple_tag
def get_following_count_by_user(user):
    followings = Following.objects.filter(follower=user)
    user_followings = []

    for following in followings:
        inside_list = False
        for user_following in user_followings:
            if following.user_tag.user.id == user_following.id:
                inside_list= True
        if not inside_list:
            user_followings.append(following.follower)

    return len(user_followings)


@register.simple_tag
def get_created_item_count_by_user(user):
    count = Item.objects.filter(creator=user).count()
    return count

@register.simple_tag
def get_updates_by_user_item(user_item):
    updates = Update.objects.filter(user=user_item.user,
                                    interaction=user_item).order_by('-timestamp')

    return updates

@register.simple_tag
def get_following_user_tags(your_user, user_item):
    tags = user_item.item.tags.all()

    following_user_tags = []
    for tag in tags:
        try:
            user_tag = User_Tag.objects.get(user=user_item.user, tag=tag)
            if your_user.is_following(user_tag):
                following_user_tags.append(user_tag)
        except:
            pass

    return following_user_tags

@register.simple_tag
def user_is_following_user_tag(user, user_tag):
    if user.is_following(user_tag):
        return True
    return False

@register.simple_tag
def get_user_tag(user, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    user_tag = User_Tag.objects.get(user=user, tag=tag)
    return user_tag

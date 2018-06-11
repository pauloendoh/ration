from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404


def get_user_tag_list(self):
    user_tag_list = User_Tag.objects.filter(user=self).order_by('-item_count')
    return user_tag_list


def get_tag_list(self):
    rating_list = User_Item.objects.filter(user=self)
    tag_list = []

    for rating in rating_list:
        for tag in rating.item.tags.all():
            if not tag in tag_list:
                tag_list.append(tag)

    return tag_list


def get_ratings_by_tag(self, tag):
    rating_query_set = User_Item.objects.filter(user=self)
    ratings = []

    for rating in rating_query_set:
        if rating.has_tag(tag):
            ratings.append(rating)
    return ratings


def get_or_create_user_item(self, item):
    try:
        user_item = User_Item.objects.get(user=self, item=item)
        return user_item
    except:
        user_item = User_Item.objects.create(user=self, item=item)
        return user_item


def get_all_updates(self):
    updates = []
    followings = Following.objects.filter(follower=self)

    for following in followings:
        user_tag = following.user_tag
        user_tag_updates = user_tag.get_update_list()
        for update in user_tag_updates:
            if update not in updates:
                updates.append(update)

    user_updates = Update.objects.filter(user=self)
    for update in user_updates:
        updates.append(update)

    updates.sort(key=lambda x: x.timestamp, reverse=True)
    return updates


def get_updates_by_tag_name(self, tag_name):
    updates = []
    updates_queryset = self.updates.all()

    if tag_name == '':
        for update in updates_queryset:
            updates.append(update)
    else:
        tag = get_object_or_404(Tag, name=tag_name)

        for update in updates_queryset:
            try:
                if update.interaction.has_tag(tag):
                    updates.append(update)
            except:
                pass
    return updates


def get_followers(self):
    followers = []

    user_tags = User_Tag.objects.filter(user=self)
    for user_tag in user_tags:
        followings = Following.objects.filter(user_tag=user_tag)

        for following in followings:
            in_list = False

            for follower in followers:
                if follower.id == following.follower.id:
                    in_list = True
            if not in_list:
                followers.append(following.follower)

    return followers


def is_following(self, user_tag):
    followings = Following.objects.filter(follower=self)
    for following in followings:
        if following.user_tag == user_tag:
            return True
    return False

def get_comparisons(user):
    pass

User.add_to_class("get_user_tag_list", get_user_tag_list)
User.add_to_class("get_tag_list", get_tag_list)
User.add_to_class("get_ratings_by_tag", get_ratings_by_tag)
User.add_to_class("get_or_create_user_item", get_or_create_user_item)
User.add_to_class("get_updates_by_tag_name", get_updates_by_tag_name)
User.add_to_class("get_followers", get_followers)
User.add_to_class("get_all_updates", get_all_updates)
User.add_to_class("is_following", is_following)
User.add_to_class("get_comparisons", get_comparisons)


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        related_name='profile',
        on_delete=models.CASCADE,
        primary_key=True
    )
    fullname = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='profile_pics', blank=True, default="profile_pics/default.png")
    bio = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    website = models.TextField(null=True, blank=True)


class Tag(models.Model):
    name = models.TextField()
    is_official = models.BooleanField(default=0)


class User_Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    item_count = models.IntegerField()
    is_private = models.NullBooleanField()

    def get_update_list(self):
        user_update_list = Update.objects.filter(user=self.user)
        update_list = []

        for update in user_update_list:
            try:
                item = update.interaction.item
                for tag in item.tags.all():
                    if tag == self.tag:
                        update_list.append(update)
            except:
                pass

        update_list.sort(key=lambda x: x.timestamp, reverse=True)

        return update_list


class Favorite_User_Tag(models.Model):
    user = models.ForeignKey(User, related_name='favorite_user_tags', on_delete=models.CASCADE)
    user_tag = models.ForeignKey(User_Tag, on_delete=models.CASCADE)


class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='items', blank=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='item_icons', blank=True, default="item_icons/default.png")

    avg_rating = models.FloatField(null=True)
    avg_interest = models.FloatField(null=True)

    def calc_average(self):
        self.avg_rating = self.user_items.all().aggregate(Avg('rating')).get('rating__avg')
        self.avg_interest = self.user_items.all().aggregate(Avg('interest')).get('interest__avg')
        self.save()

    def get_number_of_scores(self):
        return User_Item.objects.filter(item=self).count()


class User_Item(models.Model):
    user = models.ForeignKey(User, related_name='user_items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name='user_items', on_delete=models.CASCADE)
    rating = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    interest = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(3)], null=True, blank=True)

    def has_tag(self, tag):
        for x in self.item.tags.all():
            if tag == x:
                return True
        return False


class Following(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE)
    user_tag = models.ForeignKey(User_Tag, on_delete=models.CASCADE)


class Update(models.Model):
    user = models.ForeignKey(User, related_name='updates', on_delete=models.CASCADE)
    interaction = models.ForeignKey(User_Item, related_name='updates', on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)
    is_visible = models.BooleanField()

    def generate_message_by_interest(interest):
        message = ""
        if interest == 1:
            message = "not interested in:"
        if interest == 2:
            message = "interested in:"
        if interest == 3:
            message = "very interested in:"
        return message

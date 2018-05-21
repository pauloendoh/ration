from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg
from django.utils.safestring import mark_safe
from markdown import markdown


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


class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='items')

    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='item_icons', blank=True, default="item_icons/default.png")

    avg_rating = models.FloatField(null=True)
    avg_interest = models.FloatField(null=True)

    def calc_average(self):
        self.avg_rating = self.user_items.all().aggregate(Avg('rating')).get('rating__avg')
        self.avg_interest = self.user_items.all().aggregate(Avg('interest')).get('interest__avg')
        self.save()


class User_Item(models.Model):
    user = models.ForeignKey(User, related_name='user_items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name='user_items', on_delete=models.CASCADE)
    rating = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    interest = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(3)], null=True, blank=True)


class Taglist(models.Model):
    user = models.ForeignKey(User, related_name='taglists', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    tags = models.ManyToManyField(Tag)
    description = models.TextField(blank=True, null=True)
    is_private = models.BooleanField()
    is_main = models.BooleanField()

    def get_update_list(self):
        user = self.user
        user_update_list = Update.objects.filter(user=user)
        update_list = []

        for update in user_update_list:
            try:
                item = update.interaction.item
                for tag in item.tags.all():
                    if tag in self.tags.all():
                        update_list.append(update)
            except:
                pass

        update_list.sort(key=lambda x: x.timestamp, reverse=True)

        return update_list



class Following(models.Model):
    follower = models.ForeignKey(User, related_name='followings', on_delete=models.CASCADE)
    taglist = models.ForeignKey(Taglist, related_name='followings', on_delete=models.CASCADE)


class Log(models.Model):
    taglist = models.ForeignKey(Taglist, related_name='logs', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField()


class Update(models.Model):
    user = models.ForeignKey(User, related_name='updates', on_delete=models.CASCADE)
    interaction = models.ForeignKey(User_Item, related_name='updates', on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)


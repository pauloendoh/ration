from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg


class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    tag = models.CharField(max_length=30, )

    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='item_icons', null=True, blank=True)

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

class User_Item_Log(models.Model):
    user_item = models.ForeignKey(User_Item, related_name='logs', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
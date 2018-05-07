from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User

from core.models import Item, User_Item


class SignUpForm(UserCreationForm):
    email = forms.CharField(max_length=254, required=True, widget=forms.EmailInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description']

class UserItemForm(forms.ModelForm):
    rating = forms.FloatField(widget=forms.NumberInput(attrs={'max': '5', 'min':'1'}))
    interest = forms.FloatField(widget=forms.NumberInput(attrs={'max': '3', 'min':'1'}))

    class Meta:
        model = User_Item
        fields = ['rating', 'interest']
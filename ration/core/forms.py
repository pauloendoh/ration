from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User

from core.models import Item, User_Item, Profile


class SignUpForm(UserCreationForm):
    email = forms.CharField(max_length=254, required=True, widget=forms.EmailInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ItemForm(forms.ModelForm):
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': "Separate tags with ';'"}))

    class Meta:
        model = Item
        fields = ['name', 'tags', 'url', 'description', 'image']


class UserItemForm(forms.ModelForm):
    class Meta:
        model = User_Item
        fields = ['rating', 'interest']

class UpdateScoreForm(forms.ModelForm):
    class Meta:
        model = User_Item
        fields = ['rating']

class UpdateInterestForm(forms.ModelForm):
    class Meta:
        model = User_Item
        fields = ['interest']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['fullname', 'picture', 'bio', 'location', 'website']

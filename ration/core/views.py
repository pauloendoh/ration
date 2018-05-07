from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from core.forms import SignUpForm, ItemForm, UserItemForm
from core.models import Item, User_Item


def home(request):
    items = Item.objects.all()
    return render(request, 'home.html', {'items': items})

def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                user = form.save()
                auth_login(request, user)
                return redirect('home')
        else:
            form = SignUpForm()
        return render(request, 'signup.html', {'form': form})

def login(request):
    #TODO
    pass

def user(request, username):
    user = get_object_or_404(User, username=username)

    return render(request, 'user.html', {'user': user})

@login_required
def create_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.creator = request.user
            post.save()
            return redirect('home')
    else:
        form = ItemForm()
    return render(request, 'create_item.html', {'form': form})

def item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if request.method == 'POST':
        form = UserItemForm(request.POST)
        if form.is_valid():
            user = request.user

            if User_Item.objects.filter(user=user, item=item).count() > 0:
                user_item = User_Item.objects.filter(user=user, item=item).first()
                user_item.rating = form.cleaned_data['rating']
                user_item.interest = form.cleaned_data['interest']

            else:
                user_item = form.save(commit=False)
                user_item.user = user
                user_item.item = item

            user_item.save()
            return redirect('item', item_id)
    else:
        form = UserItemForm()
    return render(request, 'item.html', {'item':item, 'form': form, })
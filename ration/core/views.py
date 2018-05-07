from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from core.forms import SignUpForm, ItemForm
from core.models import Item


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
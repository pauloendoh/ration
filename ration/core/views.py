from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from core.forms import SignUpForm, ItemForm, UserItemForm
from core.models import Item, User_Item, User_Item_Log


def home(request):
    return render(request, 'home.html')

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

    user_item_list = User_Item.objects.filter(user=user)
    logs = []
    for user_item in user_item_list:
        for log in user_item.logs.all():
            logs.append(log)

    return render(request, 'user.html', {'user': user, 'logs': logs})

def user_items(request, username):
    user = get_object_or_404(User, username=username)

    user_item_list = User_Item.objects.filter(user=user)

    return render(request, 'user_items.html', {'user': user, 'user_item_list': user_item_list})



@login_required
def create_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
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
    user_item= ''

    if request.user.is_authenticated:
        user = request.user

        if User_Item.objects.filter(user=user, item=item).count() > 0:
            user_item = User_Item.objects.get(user=user, item=item)

    else:
        return render(request, 'item.html', {'item': item})

    if request.method == 'POST':
        form = UserItemForm(request.POST)
        if form.is_valid():

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

            message = user.username + " updated '" + item.name + "' (Rating: " + str(int(user_item.rating)) + "; Interest: " + str(int(user_item.interest)) + ")"
            User_Item_Log.objects.create(user_item=user_item, message=message)

            return redirect('item', item_id)
    else:
        form = UserItemForm()

    return render(request, 'item.html', {'item':item, 'form': form, 'user_item': user_item})


def edit_item(request, item_id):
    item = Item.objects.get(id=item_id)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.save()
            return redirect('item', item_id)
        else:
            return render(request, 'edit_item.html', {'item': item, 'form': form})
    else:
        return render(request, 'edit_item.html', {'item': item})

def items(request):
    items = Item.objects.all().order_by('-created_at')
    return render(request, 'items.html', {'items': items})

def search(request):
    query = request.GET.get('q')

    results = Item.objects.filter(name__icontains=query)

    return render(request, 'search.html', {'results': results})
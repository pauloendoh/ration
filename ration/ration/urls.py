"""ration URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.contrib.auth import views as auth_views

from core import views
from ration import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.login, {'template_name': 'login.html'}, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),
    path('user/<str:username>', views.user, name='user'),
    path('users', views.users, name='users'),
    path('user/<str:username>/created', views.user_created_item_list, name='user_created_item_list'),
    path('user/<str:username>/ratings', views.rating_list, name='rating_list'),
    path('user/<str:username>/compare_items', views.compare_items, name='compare_items'),
    path('create_item', views.create_item, name='create_item'),
    path('item/<int:item_id>', views.item, name='item'),
    path('edit_item/<int:item_id>', views.edit_item, name='edit_item'),
    path('delete_item/<int:item_id>', views.delete_item, name='delete_item'),
    path('items', views.items, name='items'),
    path('search', views.search, name='search'),
    path('settings', views.settings, name='settings'),
    path('follow/<int:user_tag_id>', views.follow, name='follow'),
    path('user/<str:username>/following', views.following_list, name="following_list"),
    path('user/<str:username>/followers', views.follower_list, name='follower_list'),
    path('ajax/update_interaction', views.update_interaction, name='update_interaction'),
    path('private_user_tag/<int:user_tag_id>', views.private_user_tag, name='private_user_tag'),
    path('favorite_user_tag/<int:user_tag_id>', views.favorite_user_tag, name='favorite_user_tag'),
    path('hide_update/<int:update_id>', views.hide_update, name='hide_update'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

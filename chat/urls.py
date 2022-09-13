from django import views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginto, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('chat/<uuid:chatroom>/', views.send_chatroom, name='chat_chatroom'),
    # path('chat/<str:username>/', views.send_friend, name='chat_friend'),
    path('chatroom/', views.choose_chatroom, name='chatroom'),
    path('hello/', views.say_hello, name='hello'),
    path('register/', views.auth, name='register'),
    path('validate_username', views.validate_username, name='validate_username'),
    path('get_msg', views.get_msg, name='get_msg'),
    path('add_chat', views.add_chat, name='add_chat'),
    path('add_user', views.add_user, name='add_user'),
    # path('get_msg', views.get_server_msg, name='get_msg'),
]

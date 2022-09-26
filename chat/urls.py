from django import views
from django.urls import path
from .views import *

urlpatterns = [
    path('', loginto, name='login'),
    path('logout/', user_logout, name='logout'),
    path('chat/<uuid:chatroom>/', send_chatroom, name='chat_chatroom'),
    # path('chat/<str:username>/', send_friend, name='chat_friend'),
    # path('chatroom/', choose_chatroom, name='chatroom'),
    path('chatroom/', ChooseChatroomView.as_view(), name='chatroom'),
    path('hello/', say_hello, name='hello'),
    path('register/', auth, name='register'),
    path('validate_username', validate_username, name='validate_username'),
    path('get_msg', get_msg, name='get_msg'),
    path('add_chat', add_chat, name='add_chat'),
    path('add_user', add_user, name='add_user'),
    # path('get_msg', get_server_msg, name='get_msg'),
]

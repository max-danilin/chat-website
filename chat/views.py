from multiprocessing.sharedctypes import Value
import uuid
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse

# from chat_django import chat
from .forms import ChatroomCreateForm, CompanionForm, UserRegistrationForm, UserAuthentificationForm, MessageForm, ChatroomForm
from .models import Message, Chatroom, Companion
from .client import Client, DISCONNECT_MESSAGE, SocketException

# Create your views here.

### Setting up socket server within web server ONLY for debugging purposes

# from .server import Server
# import threading
# chat_server = Server()
# thread = threading.Thread(target=chat_server.start, daemon=True)
# thread.start()
# def get_server_msg(request):
#     response = {'messages': chat_server.get_messages}
#     print(response)
#     return JsonResponse(response)

clients = []

def say_hello(request):
    return render(request, 'hello.html', {'name': request.session.get('name')})

def auth(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Successfull registration!')
            return redirect('login')
        else:
            messages.error(request, 'Registration error!')
    else:
        form = UserRegistrationForm()
    return render(request, 'index2.html', {'form': form})

def loginto(request):
    if request.method == 'POST':
        form = UserAuthentificationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                # request.session['name'] = user.get_username()
                return redirect('chatroom')
        else:
            messages.error(request, 'Authentification error!')
    else:
        form = UserAuthentificationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect("login")

def validate_username(request):
    username = request.GET.get('username', None)
    response = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(response)

def choose_chatroom(request):
    if not isinstance(request.user, User):
        return redirect("login")
    form_chatroom = ChatroomForm(request=request)
    form_companion = CompanionForm(request=request)
    if request.method == 'POST' and is_ajax(request):
        chat_query = request.POST.get('searched_chat')
        user_query = request.POST.get('searched_user')
        if chat_query:
            try:
                chat_uuid = uuid.UUID(chat_query)
                match = Chatroom.objects.filter(token=chat_uuid).filter(private=False).first()
                response = {'chatroom': match.name, 'private': match.private, 'token': match.token, 'users': match.companions.count()}
            except ValueError as exc:
                print(exc)
                response = {'chatroom': None}
        elif user_query:
            match = User.objects.filter(username=user_query).first()
            if match:
                response = {'username': match.username}
            else:
                response = {'username': None}
        print(response)
        return JsonResponse(response)
    elif request.method == 'POST':
        print(list(request.POST.items()))
        if 'create_btn' in request.POST:
            form_create_chatroom = ChatroomCreateForm(data=request.POST)
            if form_create_chatroom.is_valid():
                chat = form_create_chatroom.save()
                companion = Companion.objects.get(user=request.user)
                companion.chatroom.add(chat)
                return redirect('chatroom')
            else:
                messages.error(request, 'Inputs for creating chatroom are incorrect!')
        elif 'chat_btn' in request.POST:
            chatroom_name = request.POST.get('name')
            print('CHAT')
            return redirect('chat_chatroom', chatroom=chatroom_name)
        elif 'friend_btn' in request.POST:
            friend_name = request.POST.get('name')
            chat_private = Chatroom.objects.create(name=request.user.username+'-'+friend_name, private=True)
            companion1 = Companion.objects.get(user=request.user)
            companion1.chatroom.add(chat_private)
            companion2 = Companion.objects.get(user__username=friend_name)
            companion2.chatroom.add(chat_private)
            print('FRIEND')
            return redirect('chat_chatroom', chatroom=chat_private.token)
    else:
        form_create_chatroom = ChatroomCreateForm()
    return render(request, 'chatroom.html', {'form1': form_chatroom, 'form2': form_companion, 'form3': form_create_chatroom})

def get_client(request, chatroom=None):
    global clients
    if not clients or request.user.username not in [cl.name for cl in clients]:
        client = Client(request.user.username)
        client.chatroom = chatroom
        try:
            client.start_client()
        except SocketException:
            raise
        clients.append(client)
    else:
        client = [cl for cl in clients if cl.name == request.user.username][0]
    return client

# def send_friend(request, username):
#     request, form = send_message(request, username)
#     print('Username ', username)
#     if form == 'is_ajax':
#         return request
#     elif form == 'con_err':
#         return redirect('hello')
#     return render(request, 'chat.html', {'form': form, 'username': username})

def send_chatroom(request, chatroom):
    new_request, form = send_message(request, chatroom)
    chatroom_obj = Chatroom.objects.get(token=chatroom)
    if chatroom_obj.private:
        companion = [user.user.username for user in chatroom_obj.companions.all() if user.user.username != request.user.username][0]
        data = {'form': form, 'username': companion}
    else:
        data = {'form': form, 'chatroom': chatroom_obj.name}
    print('Chatroom ', chatroom)
    if form == 'is_ajax':
        print('AJAX')
        return new_request
    elif form == 'con_err':
        print('CONN ERR')
        return new_request
    return render(new_request, 'chat.html', data)

def send_message(request, destination):
    global clients
    if not isinstance(request.user, User):
        return redirect("login"), 'con_err'
    form = MessageForm()
    try:
        client = get_client(request, destination)
    except SocketException:
        print('EXCEPTION FROM SEND')
        return redirect('hello'), 'con_err'
    if request.method == 'POST' and is_ajax(request):
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = Message()
            msg.user = request.user
            msg.text = form.cleaned_data['text']
            print('Dest: ', destination, type(destination))
            print('Msg: ', msg.text, msg.user)
            try:
                if not isinstance(destination, uuid.UUID):
                    target = uuid.UUID(destination)
                else:
                    target = destination
                msg.chatroom = Chatroom.objects.get(token=target)
            except ValueError:
                target = destination
                msg.receiver = Companion.objects.get(user__username=target)
            f = msg.text
            try:
                if f == 'q':
                    try:
                        client.send(DISCONNECT_MESSAGE)
                    except SocketException:
                        return JsonResponse({'user': msg.user.id, 'redirect': reverse('hello')}), 'is_ajax'
                    clients.remove(client)
                else:
                    try:
                        client.send(f)
                    except SocketException:
                        return JsonResponse({'user': msg.user.id, 'redirect': reverse('hello')}), 'is_ajax'
            except OSError as osexc:
                print("Exception from send", osexc)
                return redirect('hello'), 'con_err'
            # msg.save()
            return JsonResponse({'user': msg.user.id, 'redirect': False}, status=200), 'is_ajax'
        else:
            errors = form.errors.as_json()
            return JsonResponse({'errors': errors}, status=400), 'is_ajax'
    return (request, form)

def add_chat(request):
    if request.method == 'POST':
        token = request.POST.get('add_chatroom')
        chat = Chatroom.objects.get(pk=uuid.UUID(token))
        companion = Companion.objects.get(user=request.user)
        if chat not in companion.chatroom.all():
            companion.chatroom.add(chat)
    return redirect('chatroom')

def add_user(request):
    if request.method == 'POST':
        friend_name = request.POST.get('add_user')
        friend = Companion.objects.get(user__username=friend_name)
        companion = Companion.objects.get(user=request.user)
        print(friend, companion)
        print(companion.friends.all())
        if not companion.friend or friend not in companion.friends.all():
            print('saving comp')
            companion.friends.add(friend)
            friend.friends.add(companion)
            # companion.friend = friend
            # companion.save()
    return redirect('chatroom')

def get_msg(request):
    global clients
    if not isinstance(request.user, User):
        return redirect("login")
    try:
        client = get_client(request)
        messages = client.get_messages
        active_members = False
        for msg in messages:
            if msg[1] == 'conn':
                active_members = int(msg[2])
                messages.remove(msg)
        response = {'messages': messages, 'connected': active_members, 'redirect': False}
    except SocketException:
        print('EXCEPTION FROM GET')
        response = {'messages': None, 'connected': False, 'redirect': reverse('hello')}
    print(response)
    return JsonResponse(response, safe=False)

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
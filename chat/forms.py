from dataclasses import field
from this import d
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django import forms
from .models import Message, Chatroom, Companion


class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class':"form-control",}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class':"form-control"}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'class':"form-control"}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
 

class UserAuthentificationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(
        label=("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )


class MessageForm(forms.ModelForm):
    # def __init__(self, user, *args, **kwargs):
    #     self.user = user
    #     super().__init__(*args, **kwargs)

    # def save(self) :
    #     message = Message.objects.

    class Meta:
        model = Message
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 1})}


class ChatroomForm(forms.Form):
    name = forms.ChoiceField(widget=forms.Select(attrs={'size': 10, 'style': 'width:200px', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        self.user = self.request.user
        avail_chat = [ch for ch in Chatroom.objects.filter(Q(companions__user=self.user) | Q(private=False)).distinct()]
        self.fields['name'].choices = list(zip([ch.token for ch in avail_chat], [ch.name for ch in avail_chat]))
        self.fields['name'].label = 'Chatrooms'


class CompanionForm(forms.Form):
    name = forms.ChoiceField(widget=forms.Select(attrs={'size': 10, 'style': 'width:200px', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        self.user = self.request.user
        avail_comp = [ch for ch in Companion.objects.filter(friend__user=self.user).all()]
        self.fields['name'].choices = list(zip([ch.user.username for ch in avail_comp], [ch.user.username for ch in avail_comp]))
        self.fields['name'].label = 'Friends'


class ChatroomCreateForm(forms.ModelForm):
    class Meta:
        model = Chatroom
        fields = ['name', 'private']
        widgets = {'name': forms.TextInput(attrs={'class':"form-control"})}
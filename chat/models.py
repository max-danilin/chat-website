import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Chatroom(models.Model):
    name = models.CharField(max_length=255)
    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    private = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class Companion(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chatroom = models.ManyToManyField(Chatroom, related_name='companions', blank=True)
    friend = models.ForeignKey('self', on_delete=models.CASCADE, related_name='friends', blank=True, null=True)

    def __str__(self) -> str:
        return self.user.username


class Message(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    text = models.TextField()
    time = models.DateTimeField(auto_now_add=True)
    chatroom = models.ForeignKey(Chatroom, on_delete=models.CASCADE, related_name='message_chat', blank=True)
    receiver = models.ForeignKey(Companion, on_delete=models.CASCADE, related_name='message_comp', blank=True)

    def __str__(self) -> str:
        if self.chatroom:
            return f'Message: {self.text}\nFrom user {self.user.username} from chatroom {self.chatroom.name}.'
        elif self.receiver:
            return f'Message: {self.text}\nFrom user {self.user.username} to friend {self.receiver.user.username}.'
        else:
            return f'Message: {self.text}\nFrom user {self.user.username}.'
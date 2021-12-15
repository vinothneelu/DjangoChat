from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
active_roles=(
    ("user", "user"),
    ("manager", "manager"),
    ("admin", "admin")
)

class profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=120, choices=active_roles, default="user")
    chatrole = models.CharField(max_length=120,choices=active_roles, default="user")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()



#chat group
class ChatGroup(models.Model):
    group_name = models.CharField(max_length=300,null=False,blank=False,unique=True)
    members = models.ManyToManyField(User, through="Participants")
    role = models.CharField(max_length=300,default="user")
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now=True)
    modified_at = models.DateField(auto_now=True)


class Participants(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    group = models.ForeignKey(ChatGroup,on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now=True)
    modified_at = models.DateField(auto_now=True)


class ChatMessage(models.Model):
    message = models.CharField(max_length=500,null=False,blank=False)
    sender = models.ForeignKey(User,on_delete=models.DO_NOTHING,related_name="sender")
    receiver = models.ForeignKey(User,on_delete=models.DO_NOTHING,related_name="receiver")
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now=True)
    modified_at = models.DateField(auto_now=True)



class GroupChatMessage(models.Model):
    message = models.CharField(max_length=500,null=False,blank=False)
    sender = models.ForeignKey(User,on_delete=models.DO_NOTHING,related_name="sender_group")
    group_id = models.ForeignKey(ChatGroup,on_delete=models.DO_NOTHING,related_name="sender_group_id",null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now=True)
    modified_at = models.DateField(auto_now=True)


class ChatUserRole(models.Model):
    role = models.CharField(max_length=120, choices=active_roles, default="user")
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING,related_name="user_role_table")
    group = models.ManyToManyField(ChatGroup, through="GroupUserRole")


class GroupUserRole(models.Model):
    group = models.ForeignKey(ChatGroup,on_delete=models.DO_NOTHING)
    role = models.ForeignKey(ChatUserRole,on_delete=models.DO_NOTHING)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now=True)
    modified_at = models.DateField(auto_now=True)

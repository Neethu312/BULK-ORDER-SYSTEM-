

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Customer

@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    
    if created:
        Customer.objects.create(user=instance)
        print(f"Customer profile created for user: {instance.username}")


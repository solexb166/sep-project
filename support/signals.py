from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket


@receiver(post_save, sender=Ticket)
def auto_flag_reported_listing(sender, instance, created, **kwargs):
    if created and instance.reported_listing:
        if instance.category in ('Listing Report', 'Stolen Item', 'Scam/Fraud'):
            instance.reported_listing.is_flagged = True
            instance.reported_listing.save(update_fields=['is_flagged'])

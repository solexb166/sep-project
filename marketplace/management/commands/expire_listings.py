from django.core.management.base import BaseCommand
from django.utils import timezone
from marketplace.models import Listing


class Command(BaseCommand):
    help = 'Deactivate expired listings (past their expires_at date)'

    def handle(self, *args, **options):
        expired = Listing.objects.filter(
            is_active=True,
            is_sold=False,
            expires_at__lt=timezone.now()
        )
        count = expired.count()
        expired.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'Deactivated {count} expired listing(s).'))

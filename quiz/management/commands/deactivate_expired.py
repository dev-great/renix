from django.core.management.base import BaseCommand
from django.utils import timezone
from quiz.models import UserSubscription


class Command(BaseCommand):
    help = 'Deactivate all expired user subscriptions'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = UserSubscription.objects.filter(
            subscription_end_date__lt=now,
            is_active=True
        )
        count = expired.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'{count} expired subscriptions deactivated.'))

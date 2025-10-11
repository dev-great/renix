import logging
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import UserSubscription

logger = logging.getLogger(__name__)

class SubscriptionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                subscription = UserSubscription.objects.get(user=request.user)

                # Check if subscription is expired
                if subscription.subscription_end_date and subscription.subscription_end_date < timezone.now():
                    if subscription.is_active:
                        subscription.is_active = False
                        subscription.save()
                        logger.info(f"Subscription expired for user {request.user.id}")

                request.has_active_subscription = subscription.is_active
            except UserSubscription.DoesNotExist:
                request.has_active_subscription = False
            except Exception as e:
                logger.error(f"Error checking subscription for user {request.user.id}: {e}")

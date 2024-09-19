# myapp/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils import timezone
from .models import UserSubscription  

class SubscriptionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                subscription = UserSubscription.objects.get(user=request.user)
                # Check if the subscription end date has passed
                if subscription.subscription_end_date and subscription.subscription_end_date < timezone.now():
                    subscription.is_active = False  # Update the subscription status
                    subscription.save()  # Save the changes to the database
                request.has_active_subscription = subscription.is_active
            except UserSubscription.DoesNotExist:
                request.has_active_subscription = False
        else:
            request.has_active_subscription = False
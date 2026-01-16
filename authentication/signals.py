from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from utils.mailchimp import add_user_to_mailchimp


@receiver(user_signed_up)
def add_social_user_to_mailchimp(request, user, **kwargs):
    if user.email:
        add_user_to_mailchimp(
            email=user.email,
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            tags=["social-signup"]
        )

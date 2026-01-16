from django.conf import settings
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError


def add_user_to_mailchimp(email, first_name="", last_name="", tags=None):
    client = MailchimpMarketing.Client()
    client.set_config({
        "api_key": settings.MAILCHIMP_API_KEY,
        "server": settings.MAILCHIMP_SERVER_PREFIX,
    })

    data = {
        "email_address": email,
        "status": "subscribed",  # or "pending" for double opt-in
        "merge_fields": {
            "FNAME": first_name,
            "LNAME": last_name,
        },
    }

    if tags:
        data["tags"] = tags

    try:
        return client.lists.add_list_member(
            settings.MAILCHIMP_AUDIENCE_ID,
            data
        )
    except ApiClientError as error:
        # IMPORTANT: never crash signup
        print("Mailchimp error:", error.text)
        return None

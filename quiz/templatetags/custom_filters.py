# custom_filters.py
from django import template
from django.utils.html import strip_tags
from django.utils import timezone
from quiz.models import UserSubscription
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def strip_margin_left(value):
    """
    Removes inline margin-left and padding-left styles from rich text HTML
    """
    if not value:
        return value

    # Remove margin-left: XXpx; or margin-left: XXpx !important;
    cleaned = re.sub(
        r'margin-left\s*:\s*\d+px\s*!?important?\s*;?',
        '',
        value,
        flags=re.IGNORECASE
    )

    # Remove padding-left as well (optional but recommended)
    cleaned = re.sub(
        r'padding-left\s*:\s*\d+px\s*!?important?\s*;?',
        '',
        cleaned,
        flags=re.IGNORECASE
    )

    return mark_safe(cleaned)

@register.filter
def strip_empty_blocks(value):
    return mark_safe(
        re.sub(r'<(p|div)>\s*(<br\s*/?>|\s|&nbsp;)*\s*</\1>', '', value, flags=re.I)
    )


@register.filter
def remove_images(value):
    return strip_tags(value, 'img')


@register.filter(name='floatdiv')
def floatdiv(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None


@register.filter(name='floatmul')
def floatmul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return None


@register.filter
def is_subscribed(user):
    if user.is_authenticated:
        try:
            subscription = user.subscription
            return subscription.is_active and timezone.now() <= subscription.subscription_end_date
        except UserSubscription.DoesNotExist:
            return False
    return False

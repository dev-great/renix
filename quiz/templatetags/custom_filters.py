# custom_filters.py
from django import template
from django.utils.html import strip_tags
from django.utils import timezone
from quiz.models import UserSubscription

register = template.Library()


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

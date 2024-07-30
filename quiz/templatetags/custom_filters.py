# custom_filters.py
from django import template
from django.utils.html import strip_tags

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

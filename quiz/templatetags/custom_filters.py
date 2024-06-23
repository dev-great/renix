# custom_filters.py
from django import template
from django.utils.html import strip_tags

register = template.Library()


@register.filter
def remove_images(value):
    return strip_tags(value, 'img')

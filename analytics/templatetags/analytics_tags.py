from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def first_values(dictionary):
    if not dictionary:
        return []
    first_key = next(iter(dictionary))
    return list(dictionary[first_key].keys())

from django import template

register = template.Library()


@register.filter(name="split")
def split(value, key):
    """
    Returns the value turned into a list.
    """
    return value.split(key)


@register.filter(name="splitlines")
def splitlines(value):
    """
    Returns the value split by lines, removing empty lines.
    """
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return value

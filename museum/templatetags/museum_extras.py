from django import template

register = template.Library()

@register.filter(name='split')
def split(value, delimiter=','):
    """
    Разделяет строку по разделителю и возвращает список
    Использование: {{ tags|split:"," }}
    """
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]

@register.filter(name='truncatechars')
def truncatechars(value, max_length):
    """
    Обрезает строку до указанной длины
    """
    if len(value) <= max_length:
        return value
    return value[:max_length] + '...'

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Получает значение из словаря по ключу
    Использование: {{ dict|get_item:"key" }}
    """
    return dictionary.get(key)

@register.simple_tag
def get_exhibit_stats():
    """
    Возвращает статистику музея
    """
    from ..models import Exhibit
    total = Exhibit.objects.filter(status='published').count()
    featured = Exhibit.objects.filter(is_featured=True, status='published').count()
    return {
        'total': total,
        'featured': featured
    }
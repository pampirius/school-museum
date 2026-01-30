from .models import Exhibit

def museum_stats(request):
    """Добавляет статистику музея во все шаблоны"""
    total_published = Exhibit.objects.filter(status='published').count()
    
    return {
        'exhibit_count': total_published,
    }
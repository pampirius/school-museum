from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Exhibit, Category, ExhibitPhoto, Document

def home(request):
    """Перенаправление на список экспонатов"""
    return redirect('museum:exhibit_list')

def exhibit_list(request):
    """Список всех экспонатов с фильтрацией и поиском"""
    exhibits = Exhibit.objects.filter(status='published').order_by('-created_at')
    
    # Поиск
    query = request.GET.get('q')
    if query:
        exhibits = exhibits.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(inventory_number__icontains=query) |
            Q(author__icontains=query)
        )
    
    # Фильтрация по категории
    category_id = request.GET.get('category')
    if category_id:
        exhibits = exhibits.filter(category_id=category_id)
    
    # Фильтрация по тегу
    tag = request.GET.get('tag')
    if tag:
        exhibits = exhibits.filter(tags__icontains=tag)
    
    # Фильтрация по избранному
    is_featured = request.GET.get('is_featured')
    if is_featured:
        exhibits = exhibits.filter(is_featured=True)
    
    # Пагинация
    paginator = Paginator(exhibits, 12)  # 12 экспонатов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем категории для фильтра с подсчетом экспонатов
    categories = Category.objects.annotate(
        exhibit_count=Count('exhibit', filter=Q(exhibit__status='published'))
    )
    
    # Популярные теги (первые 10)
    all_tags = []
    for exhibit in Exhibit.objects.filter(status='published'):
        if exhibit.tags:
            all_tags.extend([tag.strip() for tag in exhibit.tags.split(',') if tag.strip()])
    popular_tags = sorted(set(all_tags))[:10]
    
    # Подсчет статистики
    total_exhibits = Exhibit.objects.filter(status='published').count()
    featured_count = Exhibit.objects.filter(is_featured=True, status='published').count()
    
    context = {
        'page_obj': page_obj,
        'exhibits': page_obj.object_list,
        'categories': categories,
        'popular_tags': popular_tags,
        'search_query': query or '',
        'selected_category': int(category_id) if category_id else None,
        'selected_tag': tag or '',
        'total_exhibits': total_exhibits,      # ← ДОБАВЛЕНО
        'featured_count': featured_count,      # ← ДОБАВЛЕНО
    }
    
    return render(request, 'museum/exhibit_list.html', context)

def exhibit_detail(request, pk):
    """Детальная страница экспоната"""
    exhibit = get_object_or_404(Exhibit, pk=pk)
    
    # Проверяем доступ (только опубликованные или для авторизованных)
    if exhibit.status != 'published' and not request.user.is_authenticated:
        return redirect('museum:exhibit_list')
    
    # Получаем фотографии
    photos = exhibit.photos.all()
    
    # Получаем документы
    documents = exhibit.documents.all()
    
    # Получаем похожие экспонаты (из той же категории)
    similar_exhibits = Exhibit.objects.filter(
        category=exhibit.category,
        status='published'
    ).exclude(pk=exhibit.pk)[:4]
    
    # Получаем категорию с количеством экспонатов
    if exhibit.category:
        category_with_count = Category.objects.filter(
            pk=exhibit.category.pk
        ).annotate(
            exhibit_count=Count('exhibit', filter=Q(exhibit__status='published'))
        ).first()
    else:
        category_with_count = None
    
    context = {
        'exhibit': exhibit,
        'photos': photos,
        'documents': documents,
        'similar_exhibits': similar_exhibits,
        'category_with_count': category_with_count,  # ← ДОБАВЛЕНО
    }
    
    return render(request, 'museum/exhibit_detail.html', context)

def category_list(request):
    """Список всех категорий"""
    # Аннотируем категории количеством экспонатов
    categories = Category.objects.annotate(
        exhibit_count=Count('exhibit', filter=Q(exhibit__status='published'))
    ).order_by('name')
    
    # Общая статистика
    total_exhibits = Exhibit.objects.filter(status='published').count()
    total_categories = categories.count()
    
    context = {
        'categories': categories,
        'total_exhibits': total_exhibits,     # ← ДОБАВЛЕНО
        'total_categories': total_categories, # ← ДОБАВЛЕНО
    }
    
    return render(request, 'museum/category_list.html', context)

def category_detail(request, pk):
    """Экспонаты конкретной категории"""
    category = get_object_or_404(Category, pk=pk)
    
    # Аннотируем категорию количеством экспонатов
    category = Category.objects.filter(pk=pk).annotate(
        exhibit_count=Count('exhibit', filter=Q(exhibit__status='published'))
    ).first()
    
    exhibits = Exhibit.objects.filter(category=category, status='published')
    
    # Пагинация
    paginator = Paginator(exhibits, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем другие категории для навигации
    other_categories = Category.objects.exclude(pk=pk).annotate(
        exhibit_count=Count('exhibit', filter=Q(exhibit__status='published'))
    )[:5]
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'exhibits': page_obj.object_list,
        'other_categories': other_categories,  # ← ДОБАВЛЕНО
    }
    
    return render(request, 'museum/category_detail.html', context)

# Дополнительные функции (по желанию)

def featured_exhibits(request):
    """Страница избранных экспонатов"""
    exhibits = Exhibit.objects.filter(
        is_featured=True, 
        status='published'
    ).order_by('-created_at')
    
    paginator = Paginator(exhibits, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'exhibits': page_obj.object_list,
        'title': 'Избранные экспонаты',
        'is_featured_page': True,
    }
    
    return render(request, 'museum/exhibit_list.html', context)

def search_results(request):
    """Расширенный поиск"""
    query = request.GET.get('q', '')
    
    if not query:
        return redirect('museum:exhibit_list')
    
    exhibits = Exhibit.objects.filter(status='published')
    
    # Расширенный поиск
    search_fields = [
        'title__icontains',
        'description__icontains', 
        'tags__icontains',
        'inventory_number__icontains',
        'author__icontains',
        'historical_context__icontains',
        'material__icontains',
    ]
    
    q_objects = Q()
    for field in search_fields:
        q_objects |= Q(**{field: query})
    
    exhibits = exhibits.filter(q_objects).distinct().order_by('-created_at')
    
    paginator = Paginator(exhibits, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем категории для фильтра
    categories = Category.objects.annotate(
        exhibit_count=Count('exhibit', filter=Q(exhibit__status='published'))
    )
    
    context = {
        'page_obj': page_obj,
        'exhibits': page_obj.object_list,
        'categories': categories,
        'search_query': query,
        'is_search_page': True,
    }
    
    return render(request, 'museum/exhibit_list.html', context)
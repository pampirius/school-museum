from django.urls import path
from . import views

app_name = 'museum'

urlpatterns = [
    # Главная страница музея
    path('', views.exhibit_list, name='exhibit_list'),
    
    # Детальная страница экспоната
    path('exhibit/<int:pk>/', views.exhibit_detail, name='exhibit_detail'),
    
    # Страница категории
    path('category/<int:pk>/', views.category_detail, name='category_detail'),
    
    # Страница всех категорий
    path('categories/', views.category_list, name='category_list'),
]
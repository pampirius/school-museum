from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import os

# ==================== КАТЕГОРИИ ====================
class Category(models.Model):
    """Категории экспонатов (например: Документы, Фотографии, Награды)"""
    name = models.CharField(max_length=200, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, 
                              null=True, blank=True, 
                              verbose_name="Родительская категория")
    
    # Иконка для категории (можно использовать Font Awesome классы)
    icon = models.CharField(max_length=50, blank=True, default='fas fa-box',
                           verbose_name="Иконка (Font Awesome)")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'pk': self.pk})
    
    def get_exhibit_count(self):
        """Количество экспонатов в категории"""
        return self.exhibit_set.count()


# ==================== ЭКСПОНАТЫ ====================
class Exhibit(models.Model):
    """Основная модель экспоната"""
    
    # Статусы экспоната
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('archived', 'В архиве'),
        ('repair', 'На реставрации'),
    ]
    
    # ===== ОСНОВНАЯ ИНФОРМАЦИЯ =====
    title = models.CharField(max_length=500, verbose_name="Название экспоната")
    short_description = models.CharField(max_length=300, blank=True,
                                        verbose_name="Краткое описание")
    description = models.TextField(verbose_name="Полное описание")
    
    # ===== ТЕХНИЧЕСКАЯ ИНФОРМАЦИЯ =====
    inventory_number = models.CharField(max_length=100, unique=True,
                                       verbose_name="Инвентарный номер")
    catalog_number = models.CharField(max_length=100, blank=True,
                                     verbose_name="Каталожный номер")
    barcode = models.CharField(max_length=50, blank=True,
                              verbose_name="Штрих-код")
    
    # ===== КЛАССИФИКАЦИЯ =====
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                null=True, verbose_name="Категория")
    tags = models.CharField(max_length=300, blank=True,
                           verbose_name="Ключевые слова (теги, через запятую)")
    
    # ===== ИСТОРИЧЕСКАЯ ИНФОРМАЦИЯ =====
    acquisition_date = models.DateField(null=True, blank=True,
                                       verbose_name="Дата поступления")
    acquisition_source = models.CharField(max_length=300, blank=True,
                                         verbose_name="Источник поступления")
    creation_date = models.CharField(max_length=100, blank=True,
                                    verbose_name="Дата создания (оригинала)")
    author = models.CharField(max_length=200, blank=True,
                             verbose_name="Автор/Изготовитель")
    historical_context = models.TextField(blank=True,
                                         verbose_name="Исторический контекст")
    
    # ===== ФИЗИЧЕСКИЕ ХАРАКТЕРИСТИКИ =====
    condition = models.TextField(blank=True, verbose_name="Состояние сохранности")
    storage_location = models.CharField(max_length=200, blank=True,
                                       verbose_name="Место хранения")
    size = models.CharField(max_length=100, blank=True,
                           verbose_name="Размеры (ШхВхГ)")
    weight = models.CharField(max_length=50, blank=True,
                             verbose_name="Вес")
    material = models.CharField(max_length=200, blank=True,
                               verbose_name="Материал")
    color = models.CharField(max_length=100, blank=True,
                            verbose_name="Цвет")
    
    # ===== ОЦЕНОЧНАЯ ИНФОРМАЦИЯ =====
    estimated_value = models.DecimalField(max_digits=10, decimal_places=2,
                                         null=True, blank=True,
                                         verbose_name="Оценочная стоимость")
    insurance_value = models.DecimalField(max_digits=10, decimal_places=2,
                                         null=True, blank=True,
                                         verbose_name="Страховая стоимость")
    
    # ===== СИСТЕМНЫЕ ПОЛЯ =====
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                             default='draft', verbose_name="Статус")
    is_featured = models.BooleanField(default=False, verbose_name="Показать на главной")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, related_name='created_exhibits',
                                  verbose_name="Кем создан")
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, related_name='modified_exhibits',
                                        verbose_name="Кем изменен")
    
    class Meta:
        verbose_name = "Экспонат"
        verbose_name_plural = "Экспонаты"
        ordering = ['-created_at']
        permissions = [
            ("can_publish", "Может публиковать экспонаты"),
            ("can_archive", "Может отправлять в архив"),
        ]
    
    def __str__(self):
        return f"{self.inventory_number} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('exhibit_detail', kwargs={'pk': self.pk})
    
    def get_primary_photo(self):
        """Получает главное фото экспоната"""
        primary = self.photos.filter(is_primary=True).first()
        if primary:
            return primary
        # Если нет главного, берем первое
        return self.photos.first()
    
    def get_photo_count(self):
        """Количество фотографий экспоната"""
        return self.photos.count()
    
    def get_document_count(self):
        """Количество документов экспоната"""
        return self.documents.count()


# ==================== ФОТОГРАФИИ ЭКСПОНАТА ====================
class ExhibitPhoto(models.Model):
    """Модель для хранения нескольких фотографий одного экспоната"""
    exhibit = models.ForeignKey(Exhibit, on_delete=models.CASCADE,
                               related_name='photos')
    photo = models.ImageField(upload_to='exhibit_photos/%Y/%m/%d/',
                             verbose_name="Фотография")
    title = models.CharField(max_length=200, blank=True,
                            verbose_name="Название фотографии")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_primary = models.BooleanField(default=False, verbose_name="Главное фото")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, verbose_name="Кем загружено")
    
    class Meta:
        verbose_name = "Фотография экспоната"
        verbose_name_plural = "Фотографии экспонатов"
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"Фото: {self.title or 'Без названия'} для {self.exhibit.title}"
    
    def save(self, *args, **kwargs):
        # Если это фото установлено как главное, снимаем флаг с других фото этого экспоната
        if self.is_primary:
            ExhibitPhoto.objects.filter(exhibit=self.exhibit, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


# ==================== ДОКУМЕНТЫ К ЭКСПОНАТУ ====================
class Document(models.Model):
    """Документы, связанные с экспонатом"""
    DOCUMENT_TYPES = [
        ('scan', 'Скан документа'),
        ('certificate', 'Сертификат подлинности'),
        ('manual', 'Инструкция/Руководство'),
        ('research', 'Научное исследование'),
        ('act', 'Акт приема-передачи'),
        ('other', 'Другое'),
    ]
    
    exhibit = models.ForeignKey(Exhibit, on_delete=models.CASCADE,
                               related_name='documents')
    document = models.FileField(upload_to='exhibit_docs/%Y/%m/%d/',
                               verbose_name="Файл документа")
    title = models.CharField(max_length=200, verbose_name="Название документа")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES,
                                    default='other', verbose_name="Тип документа")
    description = models.TextField(blank=True, verbose_name="Описание")
    upload_date = models.DateField(auto_now_add=True, verbose_name="Дата загрузки")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, verbose_name="Кем загружен")
    
    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ['-upload_date']
    
    def __str__(self):
        return self.title
    
    def get_file_extension(self):
        """Получить расширение файла"""
        return os.path.splitext(self.document.name)[1].lower()


# ==================== ИСТОРИЯ ИЗМЕНЕНИЙ ====================
class ExhibitHistory(models.Model):
    """История изменений экспоната (кто, когда и что изменил)"""
    ACTION_CHOICES = [
        ('created', 'Создан'),
        ('updated', 'Изменен'),
        ('published', 'Опубликован'),
        ('archived', 'Архивирован'),
        ('restored', 'Восстановлен'),
        ('photo_added', 'Добавлено фото'),
        ('document_added', 'Добавлен документ'),
        ('status_changed', 'Изменен статус'),
    ]
    
    exhibit = models.ForeignKey(Exhibit, on_delete=models.CASCADE,
                               related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES,
                             verbose_name="Действие")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  verbose_name="Кем изменено")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Когда изменено")
    description = models.TextField(blank=True, verbose_name="Описание изменения")
    changed_fields = models.JSONField(default=dict, blank=True,
                                     verbose_name="Измененные поля")
    
    class Meta:
        verbose_name = "Запись истории"
        verbose_name_plural = "История изменений"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.exhibit.title}"
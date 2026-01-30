from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Exhibit, ExhibitPhoto, Document, ExhibitHistory


# ==================== INLINE МОДЕЛИ ====================
class ExhibitPhotoInline(admin.TabularInline):
    """Фотографии внутри редактирования экспоната"""
    model = ExhibitPhoto
    extra = 1
    readonly_fields = ['photo_preview']
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', 
                              obj.photo.url)
        return "Нет фото"
    photo_preview.short_description = "Предпросмотр"


class DocumentInline(admin.TabularInline):
    """Документы внутри редактирования экспоната"""
    model = Document
    extra = 1
    fields = ['title', 'document_type', 'document', 'description']
    readonly_fields = ['upload_date']


class ExhibitHistoryInline(admin.TabularInline):
    """История изменений внутри экспоната"""
    model = ExhibitHistory
    extra = 0
    max_num = 10
    readonly_fields = ['action', 'changed_by', 'changed_at', 'description']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# ==================== АДМИН-КЛАССЫ ====================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'icon', 'get_exhibit_count']
    list_filter = ['parent']
    search_fields = ['name', 'description']
    list_editable = ['icon']
    
    def get_exhibit_count(self, obj):
        return obj.get_exhibit_count()
    get_exhibit_count.short_description = 'Кол-во экспонатов'


@admin.register(Exhibit)
class ExhibitAdmin(admin.ModelAdmin):
    # Отображение в списке
    list_display = ['inventory_number', 'title', 'category', 'status', 
                   'is_featured', 'created_at', 'created_by']
    list_filter = ['status', 'category', 'created_at', 'is_featured']
    search_fields = ['title', 'description', 'inventory_number', 
                    'catalog_number', 'tags', 'author']
    list_editable = ['status', 'is_featured']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 
                      'last_modified_by', 'get_photo_count', 'get_document_count']
    
    # Inline модели
    inlines = [ExhibitPhotoInline, DocumentInline, ExhibitHistoryInline]
    
    # Группировка полей в форме редактирования
    fieldsets = [
        ('📋 Основная информация', {
            'fields': ['title', 'short_description', 'description']
        }),
        ('🏷 Классификация', {
            'fields': ['category', 'tags', 'inventory_number', 
                      'catalog_number', 'barcode']
        }),
        ('📅 Историческая информация', {
            'fields': ['acquisition_date', 'acquisition_source',
                      'creation_date', 'author', 'historical_context'],
            'classes': ['collapse']
        }),
        ('📏 Физические характеристики', {
            'fields': ['condition', 'storage_location', 'size',
                      'weight', 'material', 'color'],
            'classes': ['collapse']
        }),
        ('💰 Оценочная информация', {
            'fields': ['estimated_value', 'insurance_value'],
            'classes': ['collapse']
        }),
        ('⚙️ Системная информация', {
            'fields': ['status', 'is_featured', 'created_at', 'updated_at',
                      'created_by', 'last_modified_by', 'get_photo_count',
                      'get_document_count'],
            'classes': ['collapse']
        }),
    ]
    
    def get_photo_count(self, obj):
        return obj.get_photo_count()
    get_photo_count.short_description = 'Фотографий'
    
    def get_document_count(self, obj):
        return obj.get_document_count()
    get_document_count.short_description = 'Документов'
    
    def save_model(self, request, obj, form, change):
        # Автоматическое заполнение created_by и last_modified_by
        if not obj.pk:
            obj.created_by = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExhibitPhoto)
class ExhibitPhotoAdmin(admin.ModelAdmin):
    list_display = ['exhibit', 'title', 'photo_preview', 'is_primary', 'uploaded_at']
    list_filter = ['is_primary', 'uploaded_at']
    search_fields = ['exhibit__title', 'title', 'description']
    list_editable = ['is_primary']
    readonly_fields = ['uploaded_at', 'uploaded_by']
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', 
                              obj.photo.url)
        return "Нет фото"
    photo_preview.short_description = "Фото"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['exhibit', 'title', 'document_type', 'upload_date', 'uploaded_by']
    list_filter = ['document_type', 'upload_date']
    search_fields = ['exhibit__title', 'title', 'description']
    readonly_fields = ['upload_date', 'uploaded_by']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExhibitHistory)
class ExhibitHistoryAdmin(admin.ModelAdmin):
    list_display = ['exhibit', 'action', 'changed_by', 'changed_at']
    list_filter = ['action', 'changed_at']
    search_fields = ['exhibit__title', 'description']
    readonly_fields = ['exhibit', 'action', 'changed_by', 'changed_at', 
                      'description', 'changed_fields']
    date_hierarchy = 'changed_at'
    
    def has_add_permission(self, request):
        return False
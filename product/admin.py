from django.contrib import admin
from django.utils.html import format_html
from .models import *


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "logo_preview")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)

    # показываем мини-превью логотипа
    def logo_preview(self, obj):
        if obj.logo:
            return f'<img src="{obj.logo.url}" style="height:40px; border-radius:5px;" />'
        return "—"

    logo_preview.allow_tags = True
    logo_preview.short_description = "Логотип"


class ProductImageInline(admin.TabularInline):  # можно заменить на StackedInline
    model = ProductImage
    extra = 1
    fields = ("image", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 5px;" />',
                obj.image.url
            )
        return "—"

    preview.short_description = "Превью"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "price", "is_available", "stock", "created_at")
    list_filter = ("brand", "category", "is_available")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)
    autocomplete_fields = ("brand", "category")

    def stock(self, obj):
        # если у тебя появится поле quantity или что-то похожее
        return getattr(obj, 'quantity', '—')

    stock.short_description = "На складе"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 80px; border-radius: 5px;" />',
                obj.image.url
            )
        return "—"

    preview.short_description = "Превью"


admin.site.register(Location)

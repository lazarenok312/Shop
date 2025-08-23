from django.contrib import admin
from .models import Profile, CartItem, Order, OrderItem
from product.models import Product


# ----------------------
# Profile
# ----------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "favorites_count")
    search_fields = ("user__username", "user__email")
    filter_horizontal = ("favorites",)

    def favorites_count(self, obj):
        return obj.favorites.count()

    favorites_count.short_description = "Избранное"


# ----------------------
# CartItem
# ----------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("profile", "product", "quantity", "total_price", "added_at")
    list_filter = ("added_at",)
    search_fields = ("profile__user__username", "product__name")


# ----------------------
# Order
# ----------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    verbose_name = "Товар в заказе"
    verbose_name_plural = "Товары в заказе"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "created_at", "status", "payment_method", "is_processed", "total_order_price")
    list_filter = ("status", "payment_method", "is_processed", "created_at")
    search_fields = ("profile__user__username",)
    inlines = [OrderItemInline]

    def total_order_price(self, obj):
        return sum(item.total_price for item in obj.items.all())
    total_order_price.short_description = "Общая сумма"

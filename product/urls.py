from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("order/create/", create_order, name="create_order"),
    path('search-suggestions/', SearchSuggestionsView.as_view(), name='search_suggestions'),

    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('wishlist/add/<int:product_id>/', views.WishlistAddView.as_view(), name='wishlist_add'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('cart/remove/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'),

    path('cart/update/<int:product_id>/', views.update_cart, name='cart_update'),

    path('cart/', views.CartAndWishlistView.as_view(), name='cart_view'),

    path('my-orders/', views.my_orders, name='my_orders'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('admin-orders/<int:order_id>/<str:action>/', views.process_order, name='process_order'),
]

from .models import Category
from accounts.models import Profile
from django.db.models import Sum
from django.db.models import Count


def cart_and_wishlist(request):
    cart_qty = 0
    wishlist_qty = 0

    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        wishlist_qty = profile.favorites.count()
        cart_qty = profile.cartitem_set.aggregate(total=Sum('quantity'))['total'] or 0

    return {
        'cart_qty': cart_qty,
        'wishlist_qty': wishlist_qty,
    }


def navbar_context(request):
    return {
        'categories': Category.objects.all(),
        'search_query': request.GET.get('q', ''),
        'selected_category': request.GET.get('category', '0'),
    }


def top_categories(request):
    categories = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('-product_count')[:5]
    return {'top_categories': categories}


def cart_context(request):
    cart_items = []
    cart_qty = 0
    cart_total = 0

    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile_cart = profile.cartitem_set.select_related('product').all()
        for item in profile_cart:
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'total_price': item.quantity * item.product.price
            })
            cart_qty += item.quantity
            cart_total += item.quantity * item.product.price
    else:
        cart = request.session.get('cart', {})
        for key, item in cart.items():
            cart_items.append({
                'product': {
                    'name': item['name'],
                    'price': item['price'],
                    'image': item.get('image', '')
                },
                'quantity': item['quantity'],
                'total_price': item['quantity'] * item['price']
            })
            cart_qty += item['quantity']
            cart_total += item['quantity'] * item['price']

    return {
        'cart_items': cart_items,
        'cart_qty': cart_qty,
        'cart_total': cart_total
    }

from django.views.generic import ListView, DetailView, TemplateView
from .models import *
from accounts.models import *
from django.db.models import Sum, Min, Max, Q, F
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from decimal import Decimal
import json
from django.views.decorators.http import require_POST
from accounts.models import CartItem
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test


class HomePageView(ListView):
    model = Product
    template_name = "product/home.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.all().select_related('category')

        q = self.request.GET.get('q', '').strip()
        category_ids = self.request.GET.getlist('category')
        sort = self.request.GET.get('sort')
        show = self.request.GET.get('show')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        discounted = self.request.GET.get('discounted')

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(category__name__icontains=q)
            )

        if category_ids and not ("0" in category_ids):
            queryset = queryset.filter(category_id__in=category_ids)

        if price_min:
            try:
                queryset = queryset.filter(price__gte=float(price_min))
            except ValueError:
                pass

        if price_max:
            try:
                queryset = queryset.filter(price__lte=float(price_max))
            except ValueError:
                pass

        if discounted == '1':
            queryset = queryset.filter(
                Q(discount__gt=0) | Q(old_price__gt=F('price'))
            )

        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'popular':
            queryset = queryset.annotate(total_in_cart=Sum('cartitem__quantity')).order_by('-total_in_cart')
        else:
            queryset = queryset.order_by('-id')

        if show:
            try:
                self.paginate_by = int(show)
            except ValueError:
                self.paginate_by = 20

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.request.user, 'profile', None)

        context['categories'] = Category.objects.all()
        context['selected_categories'] = self.request.GET.getlist('category')

        context['search_query'] = self.request.GET.get('q', '')
        context['sort'] = self.request.GET.get('sort', 'popular')
        context['show'] = self.paginate_by

        context['top_categories'] = (
            Category.objects
                .annotate(product_count=Count("products"))
                .order_by("-product_count")[:3]
        )
        context['top_products'] = Product.objects.annotate(
            total_sold=Sum('cartitem__quantity')
        ).order_by('-total_sold')[:3]

        context['new_products'] = Product.objects.filter(is_new=True).order_by('-id')[:12]

        prices = Product.objects.aggregate(min_price=Min('price'), max_price=Max('price'))
        context['min_price'] = prices['min_price'] or 0
        context['max_price'] = prices['max_price'] or 0
        context['selected_min_price'] = self.request.GET.get('price_min', context['min_price'])
        context['selected_max_price'] = self.request.GET.get('price_max', context['max_price'])

        cart_items = []
        cart_qty = 0
        cart_total = 0
        if profile:
            profile_cart = profile.cartitem_set.select_related('product').all()
            for item in profile_cart:
                cart_items.append({'product': item.product, 'quantity': item.quantity})
                cart_qty += item.quantity
                cart_total += item.quantity * item.product.price

        context['cart_items'] = cart_items
        context['cart_qty'] = cart_qty
        context['cart_total'] = cart_total

        wishlist_items = []
        if profile:
            wishlist_items = list(profile.favorites.all())

        context['wishlist_items'] = wishlist_items
        context['wishlist_qty'] = len(wishlist_items)

        return context


class SearchSuggestionsView(View):
    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        category_id = request.GET.get('category', '0')
        suggestions = []

        if q:
            products = Product.objects.filter(name__icontains=q)
            if category_id != '0':
                products = products.filter(category_id=category_id)
            products = products[:5]
            suggestions = [p.name for p in products]
        else:
            products = Product.objects.all()
            if category_id != '0':
                products = products.filter(category_id=category_id)
            products = products[:5]
            suggestions = [p.name for p in products]

        return JsonResponse({'suggestions': suggestions})


class CategoryListView(ListView):
    model = Category
    template_name = 'product/category_list.html'
    context_object_name = 'categories'


class CategoryDetailView(DetailView):
    model = Category
    template_name = "product/category_detail.html"
    context_object_name = "category"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.object.products.all()
        context['products'] = products
        context['has_products'] = products.exists()
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product/product_detail.html'
    context_object_name = 'product'


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
    if quantity < 1:
        quantity = 1

    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            profile=profile,
            product=product,
            defaults={"quantity": quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        cart_qty = CartItem.objects.filter(profile=profile).aggregate(
            total=Sum('quantity')
        )['total'] or 0

    else:
        cart = request.session.get('cart', {})

        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += quantity
        else:
            cart[str(product_id)] = {
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
            }

        request.session['cart'] = cart
        request.session.modified = True
        cart_qty = sum(item['quantity'] for item in cart.values())

    return JsonResponse({
        'success': True,
        'message': f'{product.name} добавлен в корзину',
        'cart_qty': cart_qty,
    })


@method_decorator(login_required, name='dispatch')
class WishlistAddView(View):
    def post(self, request, product_id):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        product = get_object_or_404(Product, id=product_id)

        if product in profile.favorites.all():
            profile.favorites.remove(product)
            action = 'removed'
        else:
            profile.favorites.add(product)
            action = 'added'

        wishlist_qty = profile.favorites.count()
        return JsonResponse({'success': True, 'action': action, 'wishlist_qty': wishlist_qty})


@login_required
def remove_from_wishlist(request, product_id):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)
    profile.favorites.remove(product)
    return redirect('cart_view')


@method_decorator(login_required, name='dispatch')
class CartAndWishlistView(TemplateView):
    template_name = 'product/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)

        cart_items = profile.cartitem_set.select_related('product').all()
        context['cart_items'] = cart_items
        context['cart_qty'] = sum(item.quantity for item in cart_items)
        context['cart_total'] = sum(Decimal(item.total_price) for item in cart_items)

        wishlist_items = profile.favorites.all()
        context['wishlist_items'] = wishlist_items
        context['wishlist_qty'] = wishlist_items.count()

        return context


def _cart_total(profile) -> Decimal:
    items = profile.cartitem_set.select_related('product')
    return sum((ci.quantity * ci.product.price) for ci in items) or Decimal('0.00')


@require_POST
@login_required
def update_cart(request, product_id):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, pk=product_id)
    cart_item, _ = CartItem.objects.get_or_create(profile=profile, product=product)

    action = request.POST.get('action')
    if not action and request.body:
        try:
            action = json.loads(request.body.decode('utf-8')).get('action')
        except Exception:
            action = None

    removed = False
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            removed = True
    else:
        return JsonResponse({'status': 'error', 'message': 'Unknown action'}, status=400)

    total = sum((ci.quantity * ci.product.price) for ci in profile.cartitem_set.all())

    if removed:
        return JsonResponse({
            'status': 'success',
            'removed': True,
            'cart_total': f'{total:.2f}',
        })

    item_total = cart_item.quantity * cart_item.product.price
    return JsonResponse({
        'status': 'success',
        'removed': False,
        'quantity': cart_item.quantity,
        'item_total': f'{item_total:.2f}',
        'cart_total': f'{total:.2f}',
    })


@require_POST
@login_required
def remove_cart_item(request, product_id):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    CartItem.objects.filter(profile=profile, product_id=product_id).delete()
    return redirect('cart_view')


def get_top_selling_products():
    return Product.objects.annotate(
        total_sold=Sum('cartitem__quantity')
    ).order_by('-total_sold')[:3]


class CheckoutView(TemplateView):
    template_name = 'product/checkout.html'


@login_required
@require_POST
def create_order(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    cart_items = profile.cartitem_set.select_related("product")

    if not cart_items.exists():
        messages.error(request, "Ваша корзина пуста")
        return redirect("cart_view")

    full_name = request.POST.get("full_name")
    phone = request.POST.get("phone")
    payment_method = request.POST.get("payment_method")

    order = Order.objects.create(
        profile=profile,
        full_name=full_name,
        phone=phone,
        payment_method=payment_method
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            name=item.product.name,
            price=item.product.price,
            quantity=item.quantity
        )

    cart_items.delete()

    messages.success(request, "Ваш заказ успешно оформлен!")

    return redirect("home")


def admin_required(user):
    return user.is_staff


@login_required
@user_passes_test(admin_required)
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'orders/admin_orders.html', {'orders': orders})


@login_required
def my_orders(request):
    orders = request.user.profile.orders.all().order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})


@login_required
@user_passes_test(admin_required)
def process_order(request, order_id, action):
    order = get_object_or_404(Order, id=order_id)
    if action == 'accept':
        order.status = 'accepted'
        order.is_processed = True
    elif action == 'complete':
        order.status = 'completed'
    elif action == 'cancel':
        order.status = 'canceled'
    order.save()
    return redirect('admin_orders')

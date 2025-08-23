from django.db import models
from django.contrib.auth.models import User
from product.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorites = models.ManyToManyField(Product, blank=True, related_name='favorited_by')

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class CartItem(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'product')

    @property
    def total_price(self):
        return self.quantity * self.product.price  # Decimal

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('accepted', 'Принят'),
        ('completed', 'Завершён'),
        ('canceled', 'Отменён'),
    ]

    PAYMENT_METHODS = [
        ('bank', 'Прямой банковский перевод'),
        ('check', 'Оплата чеком'),
        ('paypal', 'PayPal'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="orders")
    full_name = models.CharField("ФИО", max_length=255, blank=True, null=True)
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='bank',
        verbose_name="Метод оплаты"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')

    def __str__(self):
        return f"Заказ #{self.id} ({self.profile.user.username})"

    def total_price(self):
        """Сумма всех товаров в заказе"""
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)  # сохраняем название на момент заказа
    price = models.DecimalField(max_digits=10, decimal_places=2)  # сохраняем цену на момент заказа
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.name} x {self.quantity}"

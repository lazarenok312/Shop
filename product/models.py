from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.contrib.auth.models import User


# ----------------------
# Категории товаров
# ----------------------
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название категории")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL", blank=True)
    image = models.ImageField("Картинка", upload_to="categories/", blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subcategories',
        blank=True,
        null=True,
        verbose_name="Родительская категория"
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField("Название бренда", max_length=100, unique=True)
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True)
    description = models.TextField("Описание", blank=True, null=True)
    logo = models.ImageField("Логотип", upload_to="brands/", blank=True, null=True)

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"

    def __str__(self):
        return self.name


# ----------------------
# Местоположение товара
# ----------------------
class Location(models.Model):
    name = models.CharField(max_length=255, verbose_name="Местоположение")

    class Meta:
        verbose_name = "Местоположение"
        verbose_name_plural = "Местоположения"

    def __str__(self):
        return self.name


# ----------------------
# Товар
# ----------------------
class Product(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый товар'),
        ('excellent', 'Состояние отличное'),
        ('defect', 'Есть дефекты'),
        ('marriage', 'На запчасти'),
    ]

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория",
        null=True, blank=True
    )
    name = models.CharField("Название", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True)

    description = models.TextField("Описание")
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    old_price = models.DecimalField("Старая цена", max_digits=10, decimal_places=2, blank=True, null=True)
    discount = models.PositiveIntegerField("Скидка (%)", blank=True, null=True)
    status = models.CharField(
        "Состояние товара",
        max_length=10,
        choices=STATUS_CHOICES,
        default='new'
    )
    is_available = models.BooleanField("В наличии", default=True)
    complectation = models.TextField("Комплектация", blank=True, null=True)
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name="Бренд",
        null=True, blank=True
    )
    image = models.ImageField("Картинка", upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})


# ----------------------
# Фотографии товара
# ----------------------
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Товар")
    image = models.ImageField(upload_to='product_images/', verbose_name="Фотография")

    class Meta:
        verbose_name = "Фотография товара"
        verbose_name_plural = "Фотографии товаров"

    def __str__(self):
        return f"{self.product.name} Image"

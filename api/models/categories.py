import uuid

from django.db import models


class Categories(models.Model):
    CATEGORY_TYPES = (
        ('news', 'News'),
        ('main', 'Main Page'),
    )
    global_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    name = models.CharField(max_length=30, default='')
    order = models.PositiveIntegerField(default=0, db_index=True)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='main')
    is_active = models.BooleanField(default=False)
    is_optional = models.BooleanField(default=False)
    filter_order = models.PositiveIntegerField(null=True, blank=True)
    odds_type = models.IntegerField(default=None, null=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name="subcategories",
        blank=True,
        null=True,
    )
    code = models.CharField(max_length=255, null=True)
    def __str__(self):
        return f'{self.id}: {self.name}'

    @classmethod
    def assign_filter_order_to_categories(cls, category_names):
        categories = cls.objects.filter(name__in=category_names)
        category_name_to_order = {name: order for order, name in enumerate(category_names, 1)}

        for category in categories:
            category.filter_order = category_name_to_order.get(category.name, 0)
            category.save()


__all__ = ['Categories']
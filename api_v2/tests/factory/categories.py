import uuid

import factory
from factory import LazyFunction
from factory.django import DjangoModelFactory

from api.models import Categories


class CategoriesFactory(DjangoModelFactory):
    class Meta:
        model = Categories

    global_id = LazyFunction(uuid.uuid4)
    name = factory.Faker('word')
    is_active = factory.Faker('boolean')
    is_optional = factory.Faker('boolean')
    parent = None

    @factory.post_generation
    def subcategories(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for subcategory in extracted:
                subcategory.parent = self
                subcategory.save()

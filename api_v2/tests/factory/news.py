import factory
from factory import SubFactory
from factory.django import DjangoModelFactory

from api_v2.models.news import UserNews, CuratorNews, PublisherNews
from api_v2.tests.factory.categories import CategoriesFactory
from api_v2.tests.factory.profiles import UserProfileFactory, PublishersProfileFactory


class PublisherNewsFactory(DjangoModelFactory):
    class Meta:
        model = PublisherNews

    # global_id = LazyFunction(uuid.uuid4)
    category = SubFactory(CategoriesFactory)
    profile = SubFactory(PublishersProfileFactory)
    title = factory.Faker('sentence', nb_words=6)
    status = PublisherNews.Statuses.APPROVED
    link = factory.Faker('url')
    author = factory.Faker('name')
    is_promoted = factory.Faker('boolean')
    is_featured = factory.Faker('boolean')
    promotion_order = factory.Faker('random_int', min=1, max=10)
    feature_order = factory.Faker('random_int', min=1, max=10)

    published = factory.Faker('date_time_this_year')
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.Faker('date_time_this_year')


class UserNewsFactory(DjangoModelFactory):
    class Meta:
        model = UserNews

    title = factory.Faker('sentence', nb_words=6)
    category = SubFactory(CategoriesFactory)
    profile = SubFactory(UserProfileFactory)
    is_promoted = factory.Faker('boolean')
    is_featured = factory.Faker('boolean')
    status = UserNews.Statuses.APPROVED

    published = factory.Faker('date_time_this_year')
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.Faker('date_time_this_year')


class CuratorNewsFactory(DjangoModelFactory):
    class Meta:
        model = CuratorNews

    title = factory.Faker('sentence', nb_words=6)
    category = SubFactory(CategoriesFactory)
    profile = factory.Faker('pydict', nb_elements=5)
    type = CuratorNews.Types.TEXT
    status = CuratorNews.Statuses.APPROVED
    main_prop = factory.Faker('pydict', nb_elements=3)
    props = factory.Faker('pydict', nb_elements=5)

    published = factory.Faker('date_time_this_year')
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.Faker('date_time_this_year')
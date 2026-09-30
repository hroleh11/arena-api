import uuid
import factory
from factory import SubFactory, LazyFunction
from factory.django import DjangoModelFactory
from django.contrib.contenttypes.models import ContentType
from api_v2.models.comments import Comments
from api_v2.tests.factory.profiles import UserProfileFactory
from api_v2.tests.factory.news import UserNewsFactory


class CommentResponsesFactory(DjangoModelFactory):
    class Meta:
        model = Comments

    global_id = LazyFunction(uuid.uuid4)
    profile = SubFactory(UserProfileFactory)
    text = factory.Faker('text', max_nb_chars=200)
    created_at = factory.Faker('date_time_this_year')
    updated_at = factory.Faker('date_time_this_year')
    user_news = SubFactory(UserNewsFactory)
    parent = None

    @factory.lazy_attribute
    def content_type(self):
        if self.user_news:
            return ContentType.objects.get_for_model(self.user_news.__class__)
        return None

    @factory.lazy_attribute
    def object_id(self):
        if self.user_news:
            return self.user_news.id
        return None

    @factory.post_generation
    def set_parent(self, create, extracted, **kwargs):
        """
        Allows to set a parent comment.
        """
        if extracted:
            self.parent = extracted
            self.save()

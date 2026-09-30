import pytest

from api_v2.models import Comments
from api_v2.tests.factory.comments import CommentResponsesFactory
from api_v2.tests.factory.news import UserNewsFactory
from api_v2.tests.factory.profiles import UserProfileFactory


@pytest.mark.django_db
def test_create_comment():
    profile = UserProfileFactory()
    origin_news = UserNewsFactory()
    user_response_news = UserNewsFactory(profile=profile)
    comment = CommentResponsesFactory(profile=profile, object=origin_news, user_news=user_response_news)
    child_comment = CommentResponsesFactory(object=origin_news, parent=comment)
    # child_2_comment = CommentResponsesFactory(news=origin_news, parent=child_comment)
    print(comment.__dict__)
    print(comment.object.__dict__)
    print(comment.user_news.__dict__)
    print(child_comment.__dict__)
    print()

    print(user_response_news.response_to.object.global_id)

    assert Comments.objects.count() == 2

    created_comment = Comments.objects.first()
    assert created_comment.global_id == comment.global_id
    assert created_comment.text == comment.text
    assert created_comment.profile == comment.profile
    assert created_comment.user_news == comment.user_news
    assert created_comment.parent is None

from django.urls import path

from .views import (
    MyProfileV2, ProfileDetailsV2,
    MyCategoriesSubscription, MyPublishersSubscription,
    CategoriesSubscriptionV2, PublishersSubscriptionV2,
    PublishersListV2, NewsstandListV2, VyloPublishersListV2,
    UserNewsListV2, UserNewsV2,
    CreateDraftUserV2, ActivateDraftUserV2,
    AutoFollowListV2
)

urlpatterns = [
    path('profile', MyProfileV2.as_view(), name='myprofile-details_v2'),
    path('profile/<str:unique_value>', ProfileDetailsV2.as_view(), name="profile-details_v2"),

    path('profile/categories_subscription/', MyCategoriesSubscription.as_view(), name='mycategories_subscription'),
    path('profile/categories_subscription/<str:category_id>', CategoriesSubscriptionV2.as_view()),

    path('profile/publishers_subscription/', MyPublishersSubscription.as_view(), name='mypublishers_subscription'),
    path('profile/publishers_subscription/<str:publisher_id>', PublishersSubscriptionV2.as_view()),

    path('publishers', PublishersListV2.as_view()),
    path('newsstand', NewsstandListV2.as_view()),
    path('vylo_publishers', VyloPublishersListV2.as_view()),

    path('news', UserNewsListV2.as_view(), name='news-list_v2'),
    path('news/<str:global_id>', UserNewsV2.as_view()),

    path('draft_user', CreateDraftUserV2.as_view(), name='draft-user_v2'),
    path('draft_user/<str:code>', ActivateDraftUserV2.as_view(), name='draft-user_code_v2'),

    path('auto_follow', AutoFollowListV2.as_view()),
]

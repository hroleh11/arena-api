from django.urls import path

from api.views import (
    publishers, categories, news, profile, upload, auth, search,
    env_var, creators, comments
)

urlpatterns = [
    path('profile', profile.MyProfile.as_view(), name='myprofile-details'),
    path('profile/subscriptions', profile.SubscriptionsView.as_view()),
    path('profile/following', profile.FollowingView.as_view()),
    path('profile/followers', profile.FollowersView.as_view()),
    path('profile/<str:unique_value>',
         profile.ProfileDetails.as_view(), name="profile-details"),
    path('profile_image', profile.ProfileImage.as_view()),
    path('profile_qrcode', profile.ProfileQRCode.as_view()),

    # TODO deprecate first version of subscriptions
    path('profile/categories_subscription/<str:category_id>',
         profile.CategoriesSubscription.as_view()),
    path('profile/publishers_subscription/<str:publisher_id>',
         profile.PublishersSubscription.as_view()),
    path('profile/report/', profile.ReportView.as_view(), name='profile_report'),
    path('profile/block/', profile.BlockView.as_view(), name='profile_block'),
    path('profile/block/<str:global_id>', profile.BlockDestroyView.as_view(), name='profile_destroy_block'),

    path('profile/web/<str:username>', profile.ProfileWebView.as_view()),

    path('profile/creators/socials', creators.ConnectedSocialsList.as_view(), name='creator-socials-list'),
    path('profile/creators/socials/<int:id>', creators.ConnectedSocialDestroy.as_view(), name='creator-socials-destroy'),

    path('publishers', publishers.PublishersList.as_view()),
    path('newsstand', publishers.NewsstandList.as_view()),
    path('vylo_publishers', publishers.VyloPublishersList.as_view()),

    path('categories', categories.CategoriesList.as_view(), name='categories-list'),
    path('popular/categories', categories.CategoriesNavigation.as_view()),  # Named from IOS
    path('categories/main', categories.CategoriesMain.as_view()),
    path('favorite/categories', categories.FavouriteCategoriesList.as_view()),
    path('subcategories/<str:global_id>', categories.SubcategoriesList.as_view()),

    path('news', news.UserNewsList.as_view(), name='news-list'),
    path('news_update/<str:global_id>', news.NewsUpdate.as_view(), name='news-details'),
    path('news_report', news.NewsReportView.as_view(), name='news-report'),

    # TODO delete this section
    path('my_columnnews', news.UserNewsList.as_view()),
    path('my_columnnews/<str:global_id>', news.UserNews.as_view()),
    path('columnnews_update/<str:global_id>', news.NewsUpdate.as_view()),
    path('columnnews_report', news.NewsReportView.as_view()),

    path('comments', comments.CommentsCreate.as_view()),
    path('comments/<str:global_id>', comments.CommentsUpdate.as_view()),

    path('search_trending', search.GlobalSearchTrending.as_view()),

    path('generate_presigned_url/<str:file_ext>', upload.UploadVideo.as_view()),
    path('generate_presigned_url_cover/<str:global_id>', upload.UpdateCoverView.as_view()),

    path('is_valid_username', auth.IsValidUsernameView.as_view()),

    path('draft_user', auth.CreateDraftUser.as_view(), name='draft-user'),
    path('draft_user/<str:code>', auth.ActivateDraftUser.as_view(), name='draft-user_code'),

    path('auto_follow', auth.AutoFollowList.as_view()),

    # path('beta_user/waitlist', beta_auth.WaitListView.as_view()),

    # path('beta_user', beta_auth.CreateBetaUser.as_view()),
    # path('beta_user/invite_friend', beta_auth.InviteUser.as_view()),
    # path('beta/invite_code', beta_auth.InviteCode.as_view()),
    # path('beta_user/waitlist', beta_auth.WaitListView.as_view()),
    # path('beta_user/<str:code>', beta_auth.ActivateBetaUser.as_view()),

    path('env_var', env_var.EnvVar.as_view()),
    path('join_link', auth.join_link),
]

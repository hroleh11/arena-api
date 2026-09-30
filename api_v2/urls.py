from django.urls import path

from api_v2.views import comments, news

urlpatterns = [
    path('comments/', comments.CommentsCreate.as_view(), name='comments-create'),
    path('comments/<str:global_id>/', comments.CommentsDetailsView.as_view(), name='comments-detail'),
    path('generate_presigned_url/', news.V2UploadUserNews.as_view(), name='generate-presigned-url'),

    path('news_update/<str:global_id>/', news.UserNewsUpdate.as_view(), name='news_update'),
]

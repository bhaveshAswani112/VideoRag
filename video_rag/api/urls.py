from django.urls import path
from .views import VideoProcessingAPIView,VideoQueryAPIView

urlpatterns = [
    path('process-video/', VideoProcessingAPIView.as_view(), name='process-video'),
    path('query-video/', VideoQueryAPIView.as_view(), name='query-video'),
]

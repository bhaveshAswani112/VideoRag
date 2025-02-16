from django.urls import path
from .views import VideoProcessingAPIView

urlpatterns = [
    path('process-video/', VideoProcessingAPIView.as_view(), name='process-video'),
]

from django.db import models






from django.db import models

class VideoMetadata(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    video_uri = models.URLField()
    transcript = models.JSONField()  
    frame_descriptions = models.JSONField() 
    created_at = models.DateTimeField(auto_now_add=True)

from django.db import models

# Create your models here.




class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

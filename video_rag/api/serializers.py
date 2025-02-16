from rest_framework import serializers

class VideoProcessingRequestSerializer(serializers.Serializer):
    video_url = serializers.URLField(required=True)

class QuerySerializer(serializers.Serializer):
    question = serializers.CharField()
from rest_framework import serializers

class VideoURLSerializer(serializers.Serializer):
    url = serializers.URLField()

class QuerySerializer(serializers.Serializer):
    question = serializers.CharField()
from rest_framework import serializers

class VideoProcessingRequestSerializer(serializers.Serializer):
    video_url = serializers.URLField(required=True)

class VideoQuerySerializer(serializers.Serializer):
    question = serializers.CharField(
        required=True,
        help_text="Search query for video content"
    )
    top_k = serializers.IntegerField(
        required=False, 
        default=3,
        min_value=1,
        max_value=10,
        help_text="Number of results to return (1-10)"
    )

    title = serializers.CharField(
        required=True,
        help_text="Used as metadata for relevant chunk extraction"
    )

import os
import asyncio
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from deepgram_captions import DeepgramConverter, webvtt
from googletrans import Translator
import webvtt as wvt
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import WebVTTFormatter

class CaptionProcessor:
    def __init__(self, deepgram_api_key=None):
        self.deepgram = DeepgramClient(deepgram_api_key) if deepgram_api_key else DeepgramClient()
        self.translator = Translator()
        
    async def _translate_vtt(self, input_file, output_file, target_lang="en"):
        """Internal method to translate WebVTT captions"""
        try:
            vtt = wvt.read(input_file)
            for caption in vtt:
                translated = await self.translator.translate(caption.text, dest=target_lang)
                caption.text = translated.text
            vtt.save(output_file)
            return True
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return False

    def _get_youtube_transcript(self, video_id, output_file):
        """Try to get native YouTube transcript"""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            formatter = WebVTTFormatter()
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatter.format_transcript(transcript))
            return True
        except Exception as e:
            print(f"YouTube transcript API failed: {str(e)}")
            return False

    def _deepgram_transcribe(self, audio_file, output_file, language="hi"):
        """Fallback to Deepgram speech-to-text"""
        try:
            with open(audio_file, "rb") as file:
                buffer_data = file.read()

            response = self.deepgram.listen.rest.v("1").transcribe_file(
                {"buffer": buffer_data},
                PrerecordedOptions(
                    model="nova-2",
                    smart_format=True,
                    language=language
                )
            )
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(webvtt(DeepgramConverter(response.to_dict())))
            return True
        except Exception as e:
            print(f"Deepgram transcription failed: {str(e)}")
            return False

    async def process_captions(self, video_id, audio_path, output_path, target_lang="en", source_lang="hi"):
        """
        Main processing method that handles:
        - YouTube transcript extraction (if available)
        - Speech-to-text fallback
        - Translation
        """
        temp_vtt = f"temp_{video_id}.vtt"
        final_output = f"translated_{output_path}"

        # Try YouTube transcript first
        if not self._get_youtube_transcript(video_id, temp_vtt):
            # Fallback to audio transcription
            if not self._deepgram_transcribe(audio_path, temp_vtt, source_lang):
                return False

        # Translate if needed
        if target_lang != source_lang:
            if not await self._translate_vtt(temp_vtt, final_output, target_lang):
                return False
            os.remove(temp_vtt)  # Cleanup temporary file
        else:
            os.rename(temp_vtt, final_output)

        print(f"Processing complete. Output at: {final_output}")
        return True

# Usage example
async def main():
    processor = CaptionProcessor()
    
    await processor.process_captions(
        video_id="ftDsSB3F5kg",
        audio_path="C:/Users/Bhavesh/Desktop/mindflix/uploads/videos/निर्देशक की भूमिका भाग - 1.f140.m4a",
        output_path="final_captions.vtt",
        target_lang="en",
        source_lang="hi"
    )

if __name__ == "__main__":
    asyncio.run(main())
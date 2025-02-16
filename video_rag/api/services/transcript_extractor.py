import os
import asyncio
import logging
from typing import Tuple, Optional
from deepgram import DeepgramClient, PrerecordedOptions
from deepgram_captions import DeepgramConverter, webvtt
from googletrans import Translator
import webvtt as wvt
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import WebVTTFormatter
from tqdm import tqdm
import aiofiles

class CaptionProcessor:
    def __init__(self, deepgram_api_key: Optional[str] = None):
        self.deepgram = DeepgramClient(deepgram_api_key) if deepgram_api_key else DeepgramClient()
        self.translator = Translator()
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    async def _translate_vtt(self, input_file: str, output_file: str, source_lang: str, target_lang: str = "en") -> bool:
        """Translate WebVTT captions from source language to target language"""
        try:
            vtt = wvt.read(input_file)
            for caption in tqdm(vtt, desc="Translating captions"):
                translated = await self.translator.translate(caption.text, src=source_lang, dest=target_lang)
                caption.text = translated.text
            vtt.save(output_file)
            return True
        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            return False

    def _get_best_transcript(self, video_id: str) -> Tuple[Optional[list], Optional[str]]:
        """Get the best available transcript with language detection"""
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try English first
            for transcript_type in ['manually_created', 'generated']:
                try:
                    transcript = getattr(transcripts, f'find_{transcript_type}_transcript')(['en'])
                    return transcript.fetch(), 'en'
                except Exception:
                    pass

            # Fallback to first available transcript
            for transcript in transcripts:
                return transcript.fetch(), transcript.language_code
            
            return None, None
        except Exception as e:
            self.logger.error(f"YouTube transcript API failed: {str(e)}")
            return None, None

    async def _save_transcript(self, transcript: list, output_file: str) -> bool:
        """Save transcript in WebVTT format"""
        try:
            formatter = WebVTTFormatter()
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
                await f.write(formatter.format_transcript(transcript))
            return True
        except Exception as e:
            self.logger.error(f"Failed to save transcript: {str(e)}")
            return False

    async def _deepgram_transcribe(self, audio_file: str, output_file: str, language: str = "hi") -> bool:
        """Fallback to Deepgram speech-to-text with specified language"""
        try:
            async with aiofiles.open(audio_file, "rb") as file:
                buffer_data = await file.read()

            response = await self.deepgram.listen.rest.v("1").transcribe_file(
                {"buffer": buffer_data},
                PrerecordedOptions(
                    model="nova-2",
                    smart_format=True,
                    language=language
                )
            )
            
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
                await f.write(webvtt(DeepgramConverter(response.to_dict())))
            return True
        except Exception as e:
            self.logger.error(f"Deepgram transcription failed: {str(e)}")
            return False

    async def process_captions(self, video_id: str, audio_path: str, output_path: str, 
                               target_lang: str = "en", fallback_lang: str = "hi") -> bool:
        """
        Processing workflow:
        1. Try to get English transcript from YouTube
        2. Fallback to any available YouTube transcript
        3. Translate non-English YouTube transcripts
        4. If all YouTube methods fail, use Deepgram with fallback language
        """
        temp_vtt = f"temp_{video_id}.vtt"
        final_output = output_path

        # Try YouTube transcripts
        transcript, detected_lang = self._get_best_transcript(video_id)
        if transcript:
            if not await self._save_transcript(transcript, temp_vtt):
                return False
            
            # Translate if not English
            if detected_lang != 'en':
                if not await self._translate_vtt(temp_vtt, final_output, detected_lang, target_lang):
                    return False
                os.remove(temp_vtt)
            else:
                os.rename(temp_vtt, final_output)
            return True

        # Fallback to Deepgram
        if not await self._deepgram_transcribe(audio_path, final_output, fallback_lang):
            return False

        # Translate Deepgram output if needed
        if fallback_lang != target_lang:
            if not await self._translate_vtt(final_output, final_output, fallback_lang, target_lang):
                return False

        self.logger.info(f"Processing complete. Output at: {final_output}")
        return True

async def main():
    processor = CaptionProcessor(deepgram_api_key="17bdd81afce172d05d26e239264c1c274e76bbfe")
    
    result = await processor.process_captions(
        video_id="UaGJdSUA_RM",
        audio_path="path/to/audio/file.m4a",
        output_path="final_captions.vtt",
        target_lang="en",
        fallback_lang="hi" 
    )
    
    if result:
        print("Caption processing completed successfully.")
    else:
        print("Caption processing failed.")

if __name__ == "__main__":
    asyncio.run(main())

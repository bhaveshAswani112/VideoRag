import os
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from deepgram_captions import DeepgramConverter, webvtt
from googletrans import Translator
import webvtt as wvt
import asyncio


def extract_audio_captions(audio_file, output_file):
    try:
        # Create a Deepgram client
        deepgram = DeepgramClient()

        with open(audio_file, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # Configure Deepgram options
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language="hi"
        )

        # Transcribe the audio file
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

        # Convert Deepgram response to WebVTT format
        transcription = DeepgramConverter(response.to_dict())
        captions = webvtt(transcription)

        # Save the WebVTT file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(captions)

        print(f"Captions successfully extracted and saved to {output_file}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")




async def translate_captions(input_file, output_file, target_language="en"):
    translator = Translator()

    # Read WebVTT file
    vtt = wvt.read(input_file)
    for caption in vtt:
        translated = await translator.translate(caption.text, dest=target_language)  # Use 'await' here
        caption.text = translated.text

    vtt.save(output_file)
    print(f"Translated captions saved to {output_file}")



# # Usage example
# if __name__ == "__main__":
#     audio_file = "C:/Users/Bhavesh/Desktop/mindflix/uploads/videos/निर्देशक की भूमिका भाग - 1.f140.m4a"
#     output_file = "C:/Users/Bhavesh/Desktop/mindflix/video_rag/captions.vtt"
#     extract_audio_captions(audio_file, output_file)
#     asyncio.run(translate_captions(output_file,"output_captions.vtt"))

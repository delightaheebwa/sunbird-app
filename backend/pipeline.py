from backend.sunbird_client import (
    transcribe_audio,
    translate_text,
    summarise_text,
    synthesize_speech,
)
import io
import wave
import time
from typing import Dict
from typing import TypedDict

from backend.errors import PipelineError, SunbirdAPIError

# because summarization can only be in English and Luganda(of which translation supports only English to local language and vice versa) I have to make the Input-transcribe/text-summarize part of the pipeline only use English. Translation and STT will use the langs common to both of them.
# won't include english because requirements state that the translation and TTS should be in a local language
LANG_CODES = {
    "Acholi": "ach",
    "Lugbara": "lgg",
    "Luganda": "lug",
    "Runyankole": "nyn",
    "Swahili": "swa",
    "Ateso": "teo",
}

VOICE_IDS = {
    "Acholi": 241,
    "Ateso": 242,
    "Runyankole": 243,
    "Lugbara": 245,
    "Swahili": 246,
    "Luganda": 248,
}


class PipelineResult(TypedDict):
    transcript: str
    summary: str
    translation: str
    truncated: bool
    audio: str
    timing: Dict[str, float]

# the serial pipeline is a design choice and every step is needed
def run_pipeline(
    target_language: str = "", text_input: str = "", audio_input: bytes = b""
) -> PipelineResult:

    def check_audio_duration(audio_bytes: bytes) -> float:
        """Returns duration in seconds"""
        # open uploaded bytes as WAV stream to calculate duration directly
        # since I am using WAV only for this project... it's not flexible however to other formats
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            frame_count = wav_file.getnframes()
            frame_rate = wav_file.getframerate()
            return frame_count / float(frame_rate)

    # transport contract between pipeline and Streamlit
    results: PipelineResult = {
        "transcript": "",
        "summary": "",
        "translation": "",
        "truncated": False,
        "audio": "",
        "timing": {
            "transcription": 0.0,
            "summarization": 0.0,
            "translation": 0.0,
            "audio_clip": 0.0,
            "total": 0.0
        }
    }

    # find out the total timing
    start = time.perf_counter()

    if audio_input != b"":
        # ensure audio length < 5 mins(300s)
        try:
            duration = check_audio_duration(audio_bytes=audio_input)
        except Exception as e:
            raise PipelineError("Could not read uploaded audio file") from e

        if duration > 300:
            raise PipelineError(
                "Audio file exceeds 5 minutes. Please upload a shorter file."
            )
        
        try:
            # find out timing for each step
            step_start = time.perf_counter()
            results["transcript"] = transcribe_audio(audio_bytes=audio_input)
            text = results["transcript"]
            results["timing"]["transcription"] = time.perf_counter() - step_start
            
        except SunbirdAPIError as e:
            raise PipelineError("Transcription failed") from e
        
    else:
        text = text_input

    try:
        step_start = time.perf_counter()
        results["summary"] = summarise_text(text=text)
        results["timing"]["summarization"] = time.perf_counter() - step_start
    except SunbirdAPIError as e:
        raise PipelineError("Summarization failed") from e

    lang_code = LANG_CODES.get(target_language)
    if not lang_code:
        raise PipelineError(f"Unsupported target language: {target_language}")

    try:
        step_start = time.perf_counter()
        results["translation"] = translate_text(
            text=results["summary"], target_language=lang_code
        )
        results["timing"]["translation"] = time.perf_counter() - step_start   
    except SunbirdAPIError as e:
        raise PipelineError("Translation failed") from e

    # TTS can only accept string of length 1-10000
    if len(results["translation"]) > 10000:
        results["translation"] = (results["translation"])[:10000]
        results["truncated"] = True
    else:
        results["truncated"] = False

    voice_id = VOICE_IDS.get(target_language)
    if not voice_id:
        raise PipelineError(f"No TTS voice configured for: {target_language}")

    try:
        step_start = time.perf_counter()
        results["audio"] = synthesize_speech(
            text=results["translation"], speaker_id=voice_id
        )
        results["timing"]["audio_clip"] = time.perf_counter() - step_start   
    except SunbirdAPIError as e:
        raise PipelineError("Speech synthesis failed") from e
    
    results["timing"]["total"] = time.perf_counter() - start


    return results

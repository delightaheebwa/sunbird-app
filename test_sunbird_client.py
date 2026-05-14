import sys
import types
import unittest
from unittest.mock import Mock, patch

dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda: None
sys.modules.setdefault("dotenv", dotenv_stub)

from backend import sunbird_client


class SunbirdClientTests(unittest.TestCase):
    @patch("backend.sunbird_client.requests.post")
    def test_transcribe_audio_uses_multipart_upload(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"audio_transcription": "hello world"}
        mock_post.return_value = mock_response

        output = sunbird_client.transcribe_audio(b"audio-bytes", "lug")

        self.assertEqual(output, "hello world")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["url"], "https://api.sunbird.ai/tasks/modal/stt")
        self.assertEqual(kwargs["data"], {"language": "lug"})
        self.assertEqual(kwargs["files"]["audio"][0], "audio.wav")
        self.assertEqual(kwargs["files"]["audio"][1], b"audio-bytes")
        self.assertEqual(kwargs["files"]["audio"][2], "audio/wav")

    @patch("backend.sunbird_client.requests.post")
    def test_translate_text_uses_translate_endpoint(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "COMPLETED",
            "output": {"translated_text": "Oli otya?"},
        }
        mock_post.return_value = mock_response

        output = sunbird_client.translate_text("How are you?", "eng", "lug")

        self.assertEqual(output, "Oli otya?")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["url"], "https://api.sunbird.ai/tasks/translate")
        self.assertEqual(
            kwargs["json"],
            {
                "source_language": "eng",
                "target_language": "lug",
                "text": "How are you?",
            },
        )

    @patch("backend.sunbird_client.requests.post")
    def test_synthesize_speech_uses_tts_request_fields(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "audio_url": "https://audio.example"}
        mock_post.return_value = mock_response

        output = sunbird_client.synthesize_speech("test text")

        self.assertEqual(output, "https://audio.example")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["url"], "https://api.sunbird.ai/tasks/modal/tts")
        self.assertEqual(
            kwargs["json"],
            {"text": "test text", "speaker_id": 248, "response_mode": "url"},
        )


if __name__ == "__main__":
    unittest.main()

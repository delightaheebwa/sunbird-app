# LocGen

**Transcribe, Summarise, Translate & Get Audio all in your local language!**

A Streamlit web application that takes English input (text or audio) and runs it through a multi-stage pipeline powered by the Sunbird AI API to produce transcripts, summaries, translations into Ugandan/East African languages, and text-to-speech audio output.

---

## Supported Languages

| Language | TTS Available |
|---|---|
| Acholi | Yes |
| Lugbara | Yes |
| Luganda | Yes |
| Runyankole | Yes |
| Ateso | Yes |
| Swahili | Yes |

---

## How It Works

The application runs a **4-stage generator pipeline** that yields results progressively as each stage completes:

```
Input (Text or WAV Audio)
        |
    [1] Transcription (STT)      Sunbird AI Speech-to-Text (if audio provided)
        |
    [2] Summarization            Sunbird AI Sunflower (summarize English text)
        |
    [3] Translation              Sunbird AI Sunflower (English -> local language)
        |
    [4] Text-to-Speech (TTS)     Sunbird AI TTS (playable audio output)
```

Each stage updates the Streamlit UI in real-time as the generator yields intermediate results.

### Architecture

- **Frontend:** Streamlit (pure Python web UI)
- **Backend:** Modular Python package (`backend/`) with typed contracts (TypedDicts)
- **API Layer:** Sunbird AI REST API (`https://api.sunbird.ai`)
- **Pipeline:** Generator-based sequential execution with typed yield states

---

## Repository Structure

```
sunbird-app/
  app.py                          Streamlit entry point (UI + pipeline runner)
  requirements.txt                Python dependencies
  .env.example                    Template for API token configuration
  .gitignore
  learnings.md                    Architecture decisions and trade-offs
  backend/
    __init__.py                   Package marker
    pipeline.py                   Core generator pipeline (4 stages)
    sunbird_client.py             Sunbird AI API client functions
    errors.py                     Custom exception classes
  tests/
    test_pipeline.py              Unit tests for pipeline logic
    test_sunbird_client.py        Unit tests for API client with mocked HTTP
```

---

## Prerequisites

- Python 3.10+
- A **Sunbird AI API token** (required to access the transcription, summarization, translation, and TTS endpoints)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/delightaheebwa/sunbird-app.git
cd sunbird-app

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your API token
cp .env.example .env
# Edit .env and set your Sunbird API token:
#   SUNBIRD_API_TOKEN=your_actual_token_here
```

---

## Usage

### Launch the app

```bash
streamlit run app.py
```

### Using the pipeline

1. Choose **Text** or **Audio file** input
2. For text: paste English content
3. For audio: upload a WAV file (max 5 minutes, English speech)
4. Select a target language for translation
5. Click **Run pipeline**

The UI will display each result progressively:
- Transcript (if audio input)
- English summary
- Translated summary
- Playable audio of the translation

### Using the pipeline programmatically

```python
from backend.pipeline import run_pipeline

# Process text input
for update in run_pipeline(
    target_language="Luganda",
    text_input="The Ugandan economy has shown steady growth over the past decade.",
):
    state = update["current_state"]
    results = update["results"]

    if state == "transcription":
        print("Transcribed:", results["transcript"])
    elif state == "summarization":
        print("Summary:", results["summary"])
    elif state == "translation":
        print("Translated:", results["translation"])
    elif state == "audio_clip":
        print("Audio URL:", results["audio"])
```

### Processing an audio file

```python
with open("speech.wav", "rb") as f:
    audio_bytes = f.read()

for update in run_pipeline(
    target_language="Swahili",
    text_input="",
    audio_input=audio_bytes,
):
    state = update["current_state"]
    results = update["results"]
    # Handle each stage...
```

---

## API Reference

All API calls are handled through the `backend/sunbird_client.py` module:

| Function | Endpoint | Description |
|---|---|---|
| `transcribe_audio()` | `/tasks/modal/stt` | Speech-to-text (WAV, English) |
| `summarise_text()` | `/tasks/sunflower_simple` | Text summarization |
| `translate_text()` | `/tasks/sunflower_simple` | Translation with instruction prompt |
| `synthesize_speech()` | `/tasks/modal/tts` | Text-to-speech with speaker ID |

All calls use Bearer token authentication via the `SUNBIRD_API_TOKEN` environment variable.

---

## Running Tests

```bash
python -m unittest discover -v
```

The test suite covers:
- Pipeline state transitions and error handling
- API client request formatting (with mocked HTTP)
- Audio duration validation
- Language/TTS voice validation

---

## Known Limitations

- **WAV-only input:** Only `.wav` audio files are accepted for transcription
- **No streaming:** The Sunbird REST APIs don't support SSE/WebSocket, so results appear after each stage completes (no partial/token-level streaming)
- **TTS bottleneck:** Speech synthesis is the slowest stage (~83s+), and the full audio must be generated before playback
- **Maximum audio length:** 5 minutes (300 seconds)
- **Translation truncation:** Translations exceeding 10,000 characters are silently truncated
- **Missing `__init__.py` in `backend/`:** (Note: added in this release — ensures reliable package imports)

---

## License

MIT

import streamlit as st
from backend.pipeline import run_pipeline
from backend.errors import PipelineError, SunbirdAPIError


st.title("LocGen\nTranscribe, Summarise & Translate all in your local language!")

input_mode = st.radio("Input type", ["Text", "Audio file"])

text_input = ""
audio_input = b""

if input_mode == "Text":
    text_input = st.text_area("Paste or type your English text here")
else:
    uploaded = st.file_uploader("Upload a 'wav' English audio file", type="wav")
    if uploaded:
        audio_input = uploaded.read()

target_language = st.selectbox(
    label="Translate summary to:",
    options=["Acholi", "Lugbara", "Luganda", "Runyankole", "Swahili", "Ateso"],
)

if st.button("Run pipeline"):
    if not text_input and not audio_input:
        st.error("Please provide text or an audio file.")
    else:
        with st.spinner("Processing..."):
            try:
                results = run_pipeline(
                    target_language=target_language,
                    text_input=text_input,
                    audio_input=audio_input,
                )
            except PipelineError as e:
                st.error(f"Processing failed: {e}")
                st.exception(e)
            except SunbirdAPIError as e:
                st.error("API error while processing. Please try again later.")
                st.exception(e)
            except Exception as e:
                st.error("An unexpected error occurred.")
                st.exception(e)
            else:
                if results["transcript"]:
                    st.subheader("Transcript")
                    st.write(results["transcript"])
                    st.write(f"Transcript timing: {results['timing']['transcription']}")
                    

                st.subheader("Summary")
                st.write(results["summary"])
                st.write(f"Transcript timing: {results['timing']['summarization']}")
                st.write(f"Translation timing: {results['timing']['translation']}")

                st.subheader("Audio")
                if results["truncated"] is True:
                    st.write("Note: Summary was truncated")
                else:
                    st.write("Summary intact! (not truncated)")
                st.audio(data=results["audio"])
                st.write(f"Audio clip timing: {results['timing']['audio_clip']}")

                st.write(f"\n\nTotal timing: {results['timing']['total']}")

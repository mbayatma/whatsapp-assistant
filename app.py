"""
WhatsApp Multilingual Assistant -- Streamlit version
------------------------------------------------------
Two tools in one page:
1. Type a message in English, get a tone-matched translation from Claude,
   and open it pre-filled in WhatsApp so you just hit send.
2. Paste in a message you received (any language) to read it in English.

Run locally:   streamlit run app.py
Deploy:        push to GitHub, then deploy on share.streamlit.io
"""

import urllib.parse

import anthropic
import streamlit as st

# ---------------------------------------------------------------------------
# The Claude client. st.secrets reads from .streamlit/secrets.toml locally,
# or from the "Secrets" box in Streamlit Cloud's settings once deployed --
# either way, your API key never gets written into this file or into git.
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

LANGUAGES = ["German", "Italian", "French", "Spanish", "Persian", "Other..."]

#four differen tones are predifined

TONES = {
    "Friendly": "casual and warm, like texting a friend",
    "Formal": "polite and professional, appropriate for a formal or business context",
    "Playful": "light, upbeat and a little playful",
    "Neutral": "clear and straightforward, neither too casual nor too formal",
}

#to prevent typing each time the phone numbers, one can predefine the frequent contacts
#country code is needed without the +sign 

CONTACTS = {
    "Add a new number": "",
    #example:"1123456789"
    # "Marco": "393331234567",
    # "Anna": "491701234567",
}


def translate(text: str, language: str, tone_description: str) -> str:
    """Ask Claude to translate `text` into `language`, matching the given
    tone rather than translating word-for-word."""
    prompt = (
        f"Translate the following WhatsApp message from English into {language}. "
        f"Match a tone that is {tone_description} -- do not translate "
        "word-for-word. Return ONLY the translated message, with no quotes, "
        "explanation, or extra text.\n\n"
        f"Message: {text}"
    )
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def translate_to_english(text: str) -> str:
    """Ask Claude to translate `text` (in whatever language it's in) into
    natural English. No source language needed -- Claude detects it."""
    prompt = (
        "Translate the following message into natural, everyday English, "
        "keeping the tone of the original rather than translating "
        "word-for-word. Return ONLY the translated message, with no quotes, "
        "explanation, or extra text.\n\n"
        f"Message: {text}"
    )
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# The page itself. Every line below just draws a widget -- Streamlit runs
# this whole file again from top to bottom on every click/keystroke.
# ---------------------------------------------------------------------------
st.title("WhatsApp Multilingual Assistant")
st.caption(
    "Type a message in English, get a tone-matched translation, "
    "and open it ready to send in WhatsApp."
)

text = st.text_area("Your message (English)", placeholder="Hey! Are we still on for coffee tomorrow?")

col1, col2 = st.columns(2)

with col1:
    language_choice = st.selectbox("Send in", LANGUAGES)
    if language_choice == "Other...":
        # Free text instead of the preset list -- translate() doesn't care,
        # it just plugs whatever string it's given into the prompt.
        language = st.text_input("Type the language (e.g. Portuguese, Turkish, Dutch...)")
    else:
        language = language_choice

with col2:
    tone_choice = st.selectbox("Tone", list(TONES.keys()) + ["Other..."])
    if tone_choice == "Other...":
        tone_description = st.text_input("Describe the tone (e.g. 'apologetic but firm')")
    else:
        tone_description = TONES[tone_choice]

if st.button("Translate"):
    if not text.strip():
        st.warning("Type a message first.")
    elif not language.strip():
        st.warning("Enter a language first.")
    elif not tone_description.strip():
        st.warning("Describe a tone first.")
    else:
        with st.spinner("Translating..."):
            # Store the result in session_state so it survives the rerun
            # that happens when you later type into the phone number box.
            st.session_state["translated"] = translate(text, language, tone_description)

# Only show the rest once we actually have a translation to work with.
if "translated" in st.session_state:
    translated = st.text_area(
        "Translated message (you can edit this before sending)",
        value=st.session_state["translated"],
    )

    st.caption(
        "Works for individual contacts only -- WhatsApp doesn't support "
        "opening an existing group chat with text pre-filled."
    )
    contact_choice = st.selectbox("Recipient", list(CONTACTS.keys()))
    if contact_choice == "Add a new number":
        phone = st.text_input(
            "Recipient's WhatsApp number (country code, digits only, e.g. 41791234567)"
        )
    else:
        # Pull the number straight from CONTACTS -- nothing to retype.
        phone = CONTACTS[contact_choice]
        st.caption(f"Sending to: {phone}")

    if phone:
        # WhatsApp's "click to chat" link: opens a chat with the text
        # already typed in, no API or business account needed.
        url = f"https://wa.me/{phone}?text={urllib.parse.quote(translated)}"
        st.link_button("Open in WhatsApp", url)

# ---------------------------------------------------------------------------
# Second, separate tool: translate an incoming message *into* English.
# This has no connection to your WhatsApp inbox -- you paste the message
# in by hand, same as you'd paste it into Google Translate.
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Translate a message you received")
st.caption("Paste in a message in any language to read it in English.")

received = st.text_area("Message you received", key="received_text")

if st.button("Translate to English"):
    if not received.strip():
        st.warning("Paste a message first.")
    else:
        with st.spinner("Translating..."):
            st.session_state["received_translation"] = translate_to_english(received)

if "received_translation" in st.session_state:
    st.text_area(
        "English translation",
        value=st.session_state["received_translation"],
        key="received_translation_box",
    )

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

from __future__ import annotations

import json
import re
import urllib.parse

import anthropic
import streamlit as st
from streamlit_local_storage import LocalStorage

PHONE_PATTERN = re.compile(r"\d{7,15}")
CONTACTS_KEY = "wa_contacts"

# ---------------------------------------------------------------------------
# The Claude client. st.secrets reads from .streamlit/secrets.toml locally,
# or from the "Secrets" box in Streamlit Cloud's settings once deployed --
# either way, your API key never gets written into this file or into git.
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# Each visitor's saved contacts live in their own browser's local storage --
# never on the server, never shared between visitors. LocalStorage() pulls
# whatever's already there into this session on first run.
local_storage = LocalStorage()

LANGUAGES = ["German", "Italian", "French", "Spanish", "Persian", "Other..."]

#four differen tones are predifined

TONES = {
    "Friendly": "casual and warm, like texting a friend",
    "Formal": "polite and professional, appropriate for a formal or business context",
    "Playful": "light, upbeat and a little playful",
    "Neutral": "clear and straightforward, neither too casual nor too formal",
}


def load_contacts() -> dict[str, str]:
    """Read this visitor's saved name -> phone number contacts back out of
    their browser's local storage."""
    raw = local_storage.getItem(CONTACTS_KEY)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {}


def save_contacts(contacts: dict[str, str]) -> None:
    """Write this visitor's contacts back to their browser's local storage."""
    local_storage.setItem(CONTACTS_KEY, json.dumps(contacts))


def translate(text: str, language: str, tone_description: str) -> str | None:
    """Ask Claude to translate `text` into `language`, matching the given
    tone rather than translating word-for-word. Returns None if Claude
    couldn't produce a translation (e.g. it didn't recognize the text)."""
    prompt = (
        f"Translate the following WhatsApp message from English into {language}. "
        f"Match a tone that is {tone_description} -- do not translate "
        "word-for-word. Return ONLY the translated message, with no quotes, "
        "explanation, or extra text.\n\n"
        f"Message: {text}"
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.content[0].text.strip()
    except (anthropic.APIError, IndexError, AttributeError):
        return None
    return result or None


def translate_to_english(text: str) -> str | None:
    """Ask Claude to translate `text` (in whatever language it's in) into
    natural English. No source language needed -- Claude detects it.
    Returns None if Claude couldn't produce a translation."""
    prompt = (
        "Translate the following message into natural, everyday English, "
        "keeping the tone of the original rather than translating "
        "word-for-word. Return ONLY the translated message, with no quotes, "
        "explanation, or extra text.\n\n"
        f"Message: {text}"
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.content[0].text.strip()
    except (anthropic.APIError, IndexError, AttributeError):
        return None
    return result or None


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
            result = translate(text, language, tone_description)
        if result is None:
            st.error(
                "Sorry, that message couldn't be translated -- it may contain "
                "a word or phrase Claude didn't recognize. Try rephrasing it."
            )
            st.session_state.pop("translated", None)
        else:
            # Store the result in session_state so it survives the rerun
            # that happens when you later type into the phone number box.
            st.session_state["translated"] = result

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
    contacts = load_contacts()
    contact_choice = st.selectbox("Recipient", ["Add a new number"] + sorted(contacts))
    if contact_choice == "Add a new number":
        phone = st.text_input(
            "Recipient's WhatsApp number (country code, digits only, e.g. 41791234567)"
        )
        if phone.strip() and PHONE_PATTERN.fullmatch(phone.strip()):
            save_name = st.text_input(
                "Save this number for next time (optional)", placeholder="e.g. Marco"
            )
            if save_name.strip() and st.button("Save contact"):
                contacts[save_name.strip()] = phone.strip()
                save_contacts(contacts)
                st.success(f"Saved {save_name.strip()} -- only visible in this browser.")
                st.rerun()
    else:
        # Pull the number straight from this browser's saved contacts.
        phone = contacts[contact_choice]
        st.caption(f"Sending to: {phone}")
        if st.button("Remove this contact"):
            contacts.pop(contact_choice, None)
            save_contacts(contacts)
            st.rerun()

    if phone:
        if not PHONE_PATTERN.fullmatch(phone.strip()):
            st.warning(
                "That doesn't look like a valid number. Enter it as the "
                "country code followed directly by the number -- digits "
                "only, no '+' and no spaces (e.g. 41791234567)."
            )
        else:
            # WhatsApp's "click to chat" link: opens a chat with the text
            # already typed in, no API or business account needed.
            url = f"https://wa.me/{phone.strip()}?text={urllib.parse.quote(translated)}"
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
            result = translate_to_english(received)
        if result is None:
            st.error(
                "Sorry, that message couldn't be translated -- it may contain "
                "a word or phrase Claude didn't recognize. Try rephrasing it."
            )
            st.session_state.pop("received_translation", None)
        else:
            st.session_state["received_translation"] = result

if "received_translation" in st.session_state:
    st.text_area(
        "English translation",
        value=st.session_state["received_translation"],
        key="received_translation_box",
    )

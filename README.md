# WhatsApp Multilingual Assistant

Two tools in one page:

1. Type a message in English, get a tone-matched translation, and open it
   pre-filled in WhatsApp so you just hit send — no copying between apps.
2. Paste in a message you received, in any language, to read it in English.

Built with **Streamlit** (pure Python, no HTML/JS to write) and uses the
**Anthropic API** to translate.

Tool 2 doesn't connect to your WhatsApp inbox in any way — you paste the
message in by hand, the same as you would with Google Translate.

**Limitation:** this works for individual contacts only. WhatsApp has no
link format for opening an *existing group chat* with text pre-filled
(only individual numbers support that), so group chats aren't supported —
you'd translate and copy-paste into those instead.

## How it works

- `app.py` is the whole app — a normal Python script that Streamlit turns
  into a web page. 
- `translate()` sends your message to Claude with a prompt asking for a
  casual WhatsApp tone rather than a literal translation.
- The "Open in WhatsApp" button builds a `wa.me` "click to chat" link —
  WhatsApp's own feature for opening a chat with text pre-filled. No
  WhatsApp Business API or Twilio needed.

## Run it locally (to test before deploying)

1. **Get a Claude API key**: [console.anthropic.com](https://console.anthropic.com)
   → sign in → "API Keys" → create one. (Separate from a normal claude.ai
   login — pay-as-you-go, but translating a short message costs a fraction
   of a cent.)

2. **Add your key locally**: copy `.streamlit/secrets.toml.example` to
   `.streamlit/secrets.toml` and paste your key in. This file is already
   in `.gitignore`, so it won't get pushed to GitHub.

3. **Install dependencies**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run it**:

   ```bash
   streamlit run app.py
   ```

   This opens the app in your browser at `http://localhost:8501`.

## Deploy it 

1. Push this folder to a new GitHub repo (public is fine, and gives you a
   real repo link for your portfolio card).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click "New app", and pick your repo and `app.py` as the main
   file.
3. Under "Advanced settings" → "Secrets", paste in:

   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```

4. Deploy. You'll get a public URL like `https://your-app-name.streamlit.app`
   — that's the link to put on your portfolio project card and to use
   yourself going forward.

## Notes

- Phone numbers for the WhatsApp link need the country code and no `+`,
  spaces, or leading `0` — e.g. a Swiss number `079 123 45 67` becomes
  `41791234567`.
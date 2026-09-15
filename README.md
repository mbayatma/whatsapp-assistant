# WhatsApp Multilingual Assistant

A small web app for writing WhatsApp messages in a language you don't
speak, and for reading and translating ones you receive in a language you don't
speak either.

**Live demo:** [whatsapp-assistant-translatemessages.streamlit.app](https://whatsapp-assistant-translatemessages.streamlit.app)

## What it does

1. **Write in English, send in anything.** Type a message, pick a
   language and a tone (friendly, formal, playful, neutral...), and
   Claude translates it — not word-for-word, but matching the tone you
   asked for. Click "Open in WhatsApp" and it's already typed into a
   chat with that contact, ready to send.
2. **Read a reply in English.** Paste in a message you received, in
   whatever language, and get a natural English translation back.
3. **Save contacts so you don't retype numbers.** Give a number a name
   once and it's remembered for next time — saved privately in your
   own browser, not on the server, so nobody else who uses the app can
   see your contacts.

Tool 2 never touches your actual WhatsApp inbox — you copy the message
in by hand, the same way you'd paste it into Google Translate.

**One limitation to know about:** this only works for individual
contacts. WhatsApp's "click to chat" links can only open a chat with a
phone number, not an existing group, so group messages still need a
manual copy-paste.

## How it's built

- `app.py` is the entire app, a single Python script that Streamlit
  turns into a web page. No separate frontend/backend to manage.
- Every translation is one call to Claude (the Anthropic API), asked
  to match a tone rather than translate literally.
- The "Open in WhatsApp" button is just a `wa.me` link — WhatsApp's
  own "click to chat" feature. No WhatsApp Business API, no Twilio,
  nothing to register.
- If Claude can't make sense of something, or a request fails, you get
  a friendly error message instead of a crash. Phone numbers are
  checked for the right format before the WhatsApp link is built.
- Saved contacts use browser local storage (via the
  `streamlit-local-storage` package) instead of a database. That
  means they're private to whoever's browser saved them and never
  pass through any shared storage — but they also won't follow you to
  a different browser or device, and clearing your browser data wipes
  them.

## Run it yourself

Want to run your own copy locally? Here's the full setup.

1. **Clone this repo:**

   ```bash
   git clone https://github.com/YOUR_USERNAME/whatsapp-assistant.git
   cd whatsapp-assistant
   ```

2. **Get a Claude API key** at [console.anthropic.com](https://console.anthropic.com)
   → sign in → "API Keys" → create one. (This is separate from a
   regular claude.ai account — it's pay-as-you-go, though translating
   a short message costs a fraction of a cent. Worth setting a monthly
   spend limit in the console's billing settings so you can't be
   surprised by a bill.)

3. **Add your key:** copy `.streamlit/secrets.toml.example` to
   `.streamlit/secrets.toml` and paste your key in. This file is
   already in `.gitignore`, so it stays on your machine and never gets
   committed.

4. **Install dependencies:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Run it:**

   ```bash
   streamlit run app.py
   ```

   This opens the app in your browser at `http://localhost:8501`.

## Deploy your own copy

1. Push your fork to your own GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in
   with GitHub, click "New app", and pick your repo and `app.py` as
   the main file.
3. Before deploying, open "Advanced settings" → "Secrets" and paste:

   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```

4. Deploy. You'll get a public URL like
   `https://your-app-name.streamlit.app`.
5. In the app's settings on Streamlit Cloud, under "Sharing", make
   sure it's set to public if you want anyone with the link to use it
   without signing in.

From then on, pushing to your repo's main branch automatically
redeploys the live app — no manual redeploy step needed.

## Notes

- Phone numbers for the WhatsApp link need the country code with no
  `+`, no spaces, and no leading `0` — e.g. a Swiss number
  `079 123 45 67` becomes `41791234567`. The app will warn you if a
  number doesn't look right.

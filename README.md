# AI Quiz & Lesson Generator (Hack to Hustle 2026)

Upload a syllabus/notes PDF → get an AI-generated quiz or lesson plan in seconds.
Built for SDG 4 (Quality Education): saves teachers time on quiz/lesson creation.

## 1. Get an API key
You need an Anthropic API key: https://console.anthropic.com/settings/keys
(New accounts get some free credit — plenty for a hackathon demo.)

## 2. Run it locally (fastest way to test)

```bash
cd quiz-generator
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # then paste your API key into .env
export ANTHROPIC_API_KEY=your_key_here   # Windows: set ANTHROPIC_API_KEY=your_key_here

python app.py
```

Open **http://localhost:5000**, upload a PDF, hit Generate.

## 3. Deploy it online (so judges can access it on their phones)

### Option A — Render.com (recommended, free tier, ~5 min)
1. Push this folder to a new GitHub repo.
2. Go to https://render.com → New → Web Service → connect your repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add environment variable: `ANTHROPIC_API_KEY` = your key.
6. Deploy. You'll get a public URL like `https://your-app.onrender.com`.

### Option B — Railway.app
1. Push to GitHub, then https://railway.app → New Project → Deploy from GitHub repo.
2. Railway auto-detects the Procfile.
3. Add `ANTHROPIC_API_KEY` under Variables.
4. Deploy → public URL is generated automatically.

### Option C — Replit (no GitHub needed, quickest for a live demo)
1. Go to https://replit.com → Create Repl → Import from a zip / upload these files.
2. In Replit's "Secrets" tab, add `ANTHROPIC_API_KEY`.
3. Click Run. Replit gives you a public URL instantly.

## How it works
1. `app.py` — Flask server: extracts text from the uploaded PDF (`pypdf`), sends it
   to Claude with a structured prompt, parses the JSON response.
2. `templates/index.html` + `static/style.css` — single-page UI, no build step needed.
3. No database — fully stateless, perfect for a quick demo.

## Customizing for your pitch
- Change `MODEL` in `app.py` if you want a different Claude model.
- Adjust `num_questions` / `difficulty` options in `index.html` if you want more controls.
- Add a "regional language" toggle by adding a language field to the form and
  passing it into `build_prompt()` — good next feature to demo live if judges ask
  "what's next" for this project.

## Troubleshooting
- **"Couldn't extract text from this PDF"** — the PDF is scanned/image-based;
  use a text-based PDF for the demo, or add OCR (`pytesseract`) as a stretch goal.
- **500 error mentioning JSON** — the model occasionally wraps output in extra
  text; the app already strips markdown fences, but if it still fails, just retry.

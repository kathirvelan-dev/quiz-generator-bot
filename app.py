import os
import json
import re
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from pypdf import PdfReader
import anthropic

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

ALLOWED_EXTENSIONS = {"pdf"}

# API key is read from the environment. Set ANTHROPIC_API_KEY before running.
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-5"  # change here if you want a different model


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(filepath, max_chars=12000):
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text += page_text + "\n"
        if len(text) > max_chars:
            break
    return text[:max_chars]


def build_prompt(syllabus_text, num_questions, difficulty, mode):
    if mode == "lesson":
        task = (
            f"Create a structured lesson plan covering the key concepts in this "
            f"material. Include: learning objectives, a concept breakdown in "
            f"teaching order, suggested time per section, and 3 discussion "
            f"questions for the class."
        )
        schema = """
{
  "title": "string",
  "objectives": ["string", ...],
  "sections": [
    {"heading": "string", "time_minutes": number, "content": "string"}
  ],
  "discussion_questions": ["string", "string", "string"]
}
"""
    else:
        task = (
            f"Create exactly {num_questions} quiz questions at {difficulty} "
            f"difficulty covering the key concepts in this material. Mix "
            f"multiple-choice and short-answer questions. For each MCQ include "
            f"4 options and mark the correct one. For short-answer, include a "
            f"model answer."
        )
        schema = """
{
  "title": "string",
  "questions": [
    {
      "type": "mcq" | "short_answer",
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct_answer": "string",
      "explanation": "string"
    }
  ]
}
"""

    return f"""You are an assistant that helps teachers save time preparing class material.

TASK: {task}

Respond with ONLY valid JSON matching this schema, no preamble, no markdown fences:
{schema}

SOURCE MATERIAL:
\"\"\"
{syllabus_text}
\"\"\"
"""


def call_claude(prompt):
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    )
    # Strip accidental markdown fences if the model adds them
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Please upload a PDF file"}), 400

    mode = request.form.get("mode", "quiz")
    num_questions = int(request.form.get("num_questions", 10))
    difficulty = request.form.get("difficulty", "mixed")

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        text = extract_text_from_pdf(filepath)
        if not text.strip():
            return jsonify({"error": "Couldn't extract text from this PDF (it may be scanned/image-based)."}), 400

        prompt = build_prompt(text, num_questions, difficulty, mode)
        result = call_claude(prompt)
        return jsonify({"ok": True, "mode": mode, "data": result})
    except json.JSONDecodeError:
        return jsonify({"error": "The AI response wasn't valid JSON. Try again."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

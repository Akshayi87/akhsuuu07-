from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import base64
import mimetypes

app = Flask(__name__)
CORS(app)  # Allow all origins (InfinityFree frontend se request aayegi)

OPENROUTER_API_KEY = os.environ.get("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", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-sonnet-4-5"  # OpenRouter pe Sonnet model

SYSTEM_PROMPT = """You are an expert AI coding assistant — powerful, precise, and helpful.
You help with all programming languages: Python, PHP, Lua, JavaScript, HTML, CSS, Java, C++, and more.
When given code or files, analyze them carefully.
Always provide complete, working code solutions.
Explain your reasoning clearly.
If asked about errors, debug thoroughly.
You are as capable as Claude Sonnet in coding tasks."""


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "AKSHU AI Backend Running ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        history = data.get("history", [])  # Previous messages for context

        if not user_message:
            return jsonify({"error": "Message empty hai bhai!"}), 400

        if not OPENROUTER_API_KEY:
            return jsonify({"error": "API Key set nahi hai server pe!"}), 500

        # Build messages array
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add history (last 10 messages for context)
        for msg in history[-10:]:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://akshu-ai.onrender.com",
            "X-Title": "AKSHU AI Assistant"
        }

        payload = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.7
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]

        return jsonify({"reply": ai_reply})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout ho gaya, dobara try karo!"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API Error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server Error: {str(e)}"}), 500


@app.route("/upload", methods=["POST"])
def upload():
    try:
        if not OPENROUTER_API_KEY:
            return jsonify({"error": "API Key set nahi hai!"}), 500

        file = request.files.get("file")
        user_message = request.form.get("message", "Is file ko analyze karo aur explain karo.")
        history = []

        if not file:
            return jsonify({"error": "Koi file nahi mili!"}), 400

        filename = file.filename
        file_content = file.read()
        mime_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Image files — send as vision
        if mime_type.startswith("image/"):
            b64_image = base64.b64encode(file_content).decode("utf-8")
            content = [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}}
            ]
        else:
            # Text/code files — read as text
            try:
                text_content = file_content.decode("utf-8")
            except UnicodeDecodeError:
                text_content = file_content.decode("latin-1", errors="replace")

            content = f"{user_message}\n\n**File: {filename}**\n```\n{text_content[:15000]}\n```"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://akshu-ai.onrender.com",
            "X-Title": "AKSHU AI Assistant"
        }

        payload = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.7
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()

        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]

        return jsonify({"reply": ai_reply, "filename": filename})

    except Exception as e:
        return jsonify({"error": f"Upload Error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

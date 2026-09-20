# TrustLabel - Gemini LLM Demo

## 1. Install

```powershell
python -m pip install -r requirements.txt
```

## 2. Create `.env`

Copy `.env.example` to `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-flash-latest
```

If your Google AI Studio account provides a different supported model, change
`GEMINI_MODEL` in `.env` without editing the Python code.

## 3. Run

```powershell
python app.py
```

Open:

http://127.0.0.1:5000

## Features

- Brand input
- Sustainability claim input
- Photo upload
- Short video upload
- Gemini multimodal analysis
- Risk indicator
- User highlights
- Potential red flags
- Evidence checklist
- Transparent rewrite
- 3D-style animated visual using CSS

## Important

The score is a preliminary AI screening indicator. It is not legal advice,
scientific certification, or proof that a company has committed wrongdoing.

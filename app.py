from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

import os
import json
import mimetypes
import tempfile
import time


# Load environment variables
load_dotenv()


# Flask application
app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


# Gemini configuration
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.1-flash-lite"
)


if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing in your .env file"
    )


# Gemini client
client = genai.Client(api_key=API_KEY)


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Clean JSON response
def clean_json(text):

    text = text.strip()

    if text.startswith("```"):

        text = text.replace("```json", "", 1)
        text = text.replace("```", "", 1).strip()

    return json.loads(text)


# Build analysis prompt
def build_prompt(brand, claim):

    return f"""
You are TrustLabel, an AI assistant for preliminary
greenwashing screening.

Brand name:
{brand or "Not provided"}

Sustainability claim or product label:
{claim or "Not provided"}

Analyze the claim carefully.

If a photo or video is attached, use it only as
supporting visual evidence.

Do not pretend that an image proves certification,
carbon footprint, recyclability, or legal compliance.

Return ONLY valid JSON using this structure:

{{
    "brand": "string",
    "score": 0,
    "risk": "Low Risk Indicator",
    "summary": "string",
    "highlights": [
        "string"
    ],
    "red_flags": [
        {{
            "phrase": "string",
            "reason": "string"
        }}
    ],
    "evidence": [
        "string"
    ],
    "rewrite": "string",
    "limitations": [
        "string"
    ]
}}

Rules:

- Score greenwashing risk from 0 to 100.
- 0 means fewer warning signs detected.
- 100 means many warning signs detected.
- Do not accuse a company of fraud.
- Explain uncertainty when evidence is missing.
- Identify vague or unsupported claims.
- Suggest evidence needed to verify the claim.
- Create an honest and transparent rewrite.
- This is a preliminary AI assessment, not certification
  or legal advice.
"""


# Gemini request with retry
def generate_with_retry(contents, max_retries=3):

    for attempt in range(max_retries):

        try:

            print(
                f"Gemini request attempt "
                f"{attempt + 1}/{max_retries}"
            )

            response = client.models.generate_content(

                model=MODEL,

                contents=contents,

                config=types.GenerateContentConfig(

                    response_mime_type="application/json"

                )

            )

            return response

        except Exception as error:

            error_message = str(error).upper()

            temporary_error = (

                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message

            )

            if temporary_error and attempt < max_retries - 1:

                wait_time = 2 ** attempt

                print(
                    f"Gemini server busy. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                print(
                    "Retry failed or permanent error occurred."
                )

                raise error


# Analyze route
@app.route("/analyze", methods=["POST"])
def analyze():

    brand = request.form.get(
        "brand",
        ""
    ).strip()

    claim = request.form.get(
        "claim",
        ""
    ).strip()

    photo = request.files.get("photo")

    video = request.files.get("video")


    has_photo = (
        photo is not None
        and photo.filename
    )

    has_video = (
        video is not None
        and video.filename
    )


    if (
        not brand
        and not claim
        and not has_photo
        and not has_video
    ):

        return jsonify({

            "error": (
                "Please enter a brand, claim, "
                "photo, or video."
            )

        }), 400


    prompt = build_prompt(
        brand,
        claim
    )

    contents = [prompt]

    temp_video_path = None


    try:

        # -----------------------------
        # PROCESS PHOTO
        # -----------------------------

        if has_photo:

            photo_bytes = photo.read()

            mime_type = (

                photo.mimetype

                or mimetypes.guess_type(
                    photo.filename
                )[0]

                or "image/jpeg"

            )


            contents.append(

                types.Part.from_bytes(

                    data=photo_bytes,

                    mime_type=mime_type

                )

            )


        # -----------------------------
        # PROCESS VIDEO
        # -----------------------------

        if has_video:

            safe_filename = secure_filename(
                video.filename
            )

            file_extension = os.path.splitext(
                safe_filename
            )[1]


            with tempfile.NamedTemporaryFile(

                delete=False,

                suffix=file_extension

            ) as temp_file:

                temp_video_path = temp_file.name


            video.save(temp_video_path)


            print(
                "Uploading video to Gemini..."
            )


            uploaded_video = client.files.upload(

                file=temp_video_path

            )


            contents.append(
                uploaded_video
            )


        # -----------------------------
        # SEND REQUEST
        # -----------------------------

        response = generate_with_retry(
            contents
        )


        # -----------------------------
        # CONVERT RESPONSE TO JSON
        # -----------------------------

        result = clean_json(
            response.text
        )


        # -----------------------------
        # DEFAULT VALUES
        # -----------------------------

        result.setdefault(

            "brand",

            brand or "Unknown brand"

        )


        result.setdefault(
            "score",
            0
        )


        result.setdefault(
            "risk",
            "Uncertain"
        )


        result.setdefault(

            "summary",

            "Review the findings and verify the evidence."

        )


        result.setdefault(
            "highlights",
            []
        )


        result.setdefault(
            "red_flags",
            []
        )


        result.setdefault(
            "evidence",
            []
        )


        result.setdefault(

            "rewrite",

            "No rewrite was generated."

        )


        result.setdefault(
            "limitations",
            []
        )


        return jsonify(
            result
        )


    except Exception as error:

        print(
            "Gemini Error:",
            repr(error)
        )


        return jsonify({

            "error": "Analysis failed",

            "details": str(error)

        }), 500


    finally:

        # -----------------------------
        # DELETE TEMPORARY VIDEO
        # -----------------------------

        if (

            temp_video_path

            and os.path.exists(
                temp_video_path
            )

        ):

            try:

                os.remove(
                    temp_video_path
                )


                print(
                    "Temporary video deleted."
                )


            except Exception as cleanup_error:

                print(

                    "Cleanup Error:",

                    cleanup_error

                )


# Run Flask application
if __name__ == "__main__":

    app.run(
        debug=True
    )
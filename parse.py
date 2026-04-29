"""
parse.py  —  AI extraction powered by Google Gemini (free tier)

Free API key:  https://aistudio.google.com/app/apikey
Set env var:   GEMINI_API_KEY=your_key_here
"""

import os
import json
import re
import google.generativeai as genai

_configured = False

def _setup():
    global _configured
    if _configured:
        return
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/app/apikey "
            "then run:  export GEMINI_API_KEY=your_key"
        )
    genai.configure(api_key=key)
    _configured = True


def _model():
    _setup()
    return genai.GenerativeModel("gemini-1.5-flash")   # free-tier model


EXTRACT_PROMPT = """\
You are a precise data extraction assistant.

WEB PAGE CONTENT:
{content}

EXTRACTION TASK:
{task}

RULES:
- Return ONLY the extracted data, nothing else.
- If multiple items match, list each on its own line.
- Preserve original formatting for prices, dates, and numbers.
- If nothing matches the task, return exactly: NO_MATCH
"""

SUMMARIZE_PROMPT = """\
Summarize the following web page content. Be structured and concise.

CONTENT:
{content}

Return:
1. A 2-3 sentence overview of the page
2. Key topics covered
3. Most important facts or data points
4. Overall tone of the page
"""


def parse_with_gemini(dom_chunks, parse_description):
    """Extract specific data from page chunks using Gemini."""
    model = _model()
    results = []

    for i, chunk in enumerate(dom_chunks, 1):
        print(f"Processing chunk {i}/{len(dom_chunks)} ...")
        prompt = EXTRACT_PROMPT.format(content=chunk, task=parse_description)
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text and text != "NO_MATCH":
                results.append(text)
        except Exception as exc:
            print(f"  Chunk {i} error: {exc}")

    return "\n\n".join(results) if results else "No matching content found."


def summarize_with_gemini(dom_chunks):
    """Generate a structured summary from the first few chunks."""
    model = _model()
    combined = "\n\n".join(dom_chunks[:3])[:12000]
    prompt = SUMMARIZE_PROMPT.format(content=combined)
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        return f"Summary failed: {exc}"

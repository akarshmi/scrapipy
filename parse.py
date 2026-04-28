from langchain_community.llms import Together
from langchain_core.prompts import ChatPromptTemplate
import os
import re

api_key = os.getenv("TOGETHER_API_KEY")

PARSE_TEMPLATE = (
    "You are an expert data extraction assistant. Extract ONLY the requested information "
    "from the web page content below. Be precise, structured, and concise.\n\n"
    "WEB PAGE CONTENT:\n{dom_content}\n\n"
    "EXTRACTION TASK: {parse_description}\n\n"
    "RULES:\n"
    "1. Extract ONLY what matches the task. Nothing extra.\n"
    "2. If extracting multiple items, use a clear list format.\n"
    "3. If nothing matches, return exactly: NO_MATCH\n"
    "4. Preserve original formatting for prices, dates, and numbers.\n"
    "5. Do NOT add commentary, preamble, or explanations."
)

SUMMARIZE_TEMPLATE = (
    "Summarize the following web page content. Be concise and structured.\n\n"
    "CONTENT:\n{dom_content}\n\n"
    "Provide:\n"
    "1. A 2-3 sentence overview\n"
    "2. Key topics covered (bullet points)\n"
    "3. Most important facts or data points\n"
    "4. Sentiment/tone of the content"
)

def _get_model(temperature=0.1, max_tokens=1024):
    if not api_key:
        raise ValueError("TOGETHER_API_KEY not set in environment")
    return Together(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=temperature,
        max_tokens=max_tokens,
        together_api_key=api_key,
    )

def parse_with_together(dom_chunks, parse_description):
    """Extract specific information from DOM chunks."""
    prompt = ChatPromptTemplate.from_template(PARSE_TEMPLATE)
    model = _get_model()
    chain = prompt | model
    parsed = []

    for i, chunk in enumerate(dom_chunks, start=1):
        print(f"Parsing chunk {i}/{len(dom_chunks)}...")
        try:
            response = chain.invoke({
                "dom_content": chunk,
                "parse_description": parse_description,
            })
            text = response.content if hasattr(response, "content") else str(response)
            text = text.strip()
            if text and text != "NO_MATCH":
                parsed.append(text)
        except Exception as e:
            print(f"  ⚠️ Chunk {i} failed: {e}")

    return "\n\n".join(parsed) if parsed else "No matching content found."


def summarize_with_together(dom_chunks):
    """Generate a structured summary of the page content."""
    prompt = ChatPromptTemplate.from_template(SUMMARIZE_TEMPLATE)
    model = _get_model(temperature=0.3, max_tokens=1500)
    chain = prompt | model

    # For summary, use first 3 chunks max to stay focused
    combined = "\n\n".join(dom_chunks[:3])
    try:
        response = chain.invoke({"dom_content": combined})
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        return f"Summary failed: {e}"

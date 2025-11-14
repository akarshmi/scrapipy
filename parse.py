from langchain_community.chat_models import ChatTogether
from langchain_core.prompts import ChatPromptTemplate
import os

# Get API key
api_key = os.getenv("TOGETHER_API_KEY")

# Prompt template
template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Follow these instructions:\n\n"
    "1. Extract only the information matching: {parse_description}.\n"
    "2. No extra explanations.\n"
    "3. Return empty string '' if no match."
)

# Load model
model = ChatTogether(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.1,
    max_tokens=512,
    together_api_key=api_key
)

# Parser
def parse_with_together(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    parsed_results = []
    for i, chunk in enumerate(dom_chunks, start=1):
        response = chain.invoke(
            {"dom_content": chunk, "parse_description": parse_description}
        )
        print(f"Parsed batch: {i}/{len(dom_chunks)}")
        parsed_results.append(response.content)

    return "\n".join(parsed_results)

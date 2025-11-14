from langchain_together import ChatTogether
from langchain_core.prompts import ChatPromptTemplate
import os

# Get API key from environment
api_key = os.getenv("TOGETHER_API_KEY")

# Prompt template
template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Please follow these instructions carefully:\n\n"
    "1. **Extract Information:** Only extract the information that directly matches the provided description: {parse_description}. "
    "2. **No Extra Content:** Do not include any additional text, comments, or explanations in your response. "
    "3. **Empty Response:** If no information matches the description, return an empty string (''). "
    "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
)

# Load model
model = ChatTogether(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.1,
    max_tokens=512,
    together_api_key=api_key
)

# Parse function
def parse_with_together(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    parsed_results = []
    for i, chunk in enumerate(dom_chunks, start=1):
        response = chain.invoke(
            {"dom_content": chunk, "parse_description": parse_description}
        )
        print(f"Parsed batch: {i} of {len(dom_chunks)}")
        parsed_results.append(response.content)  # AIMessage.content

    return "\n".join(parsed_results)

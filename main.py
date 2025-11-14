import streamlit as st
from scrape import (
    scrape_website,
    extract_body_content,
    clean_body_content,
    split_dom_content,
)
from parse import parse_with_together  # Updated parser imports

# Streamlit UI
st.title("AI Web Scraper")

# Input field for URL
url = st.text_input("Enter Website URL")

# Step 1: Scrape the Website
if st.button("Scrape Website"):
    if url:
        st.write("Scraping the website...")
        try:
            # Scrape the website
            dom_content = scrape_website(url)
            body_content = extract_body_content(dom_content)
            cleaned_content = clean_body_content(body_content)

            # Store the cleaned content in session state
            st.session_state.dom_content = cleaned_content

            # Display success message
            st.success("Website scraped successfully!")

            # Show DOM content inside an expandable box
            with st.expander("View DOM Content"):
                st.text_area("DOM Content", cleaned_content, height=300)

        except Exception as e:
            st.error(f"Error scraping website: {str(e)}")
            st.info("Please check the URL and try again. Make sure the website is accessible.")
    else:
        st.warning("Please enter a website URL")

# Step 2: Ask Questions About the DOM Content
if "dom_content" in st.session_state:
    parse_description = st.text_area("Describe what you want to parse")

    if st.button("Parse Content"):
        if parse_description:
            st.write("Parsing the content...")

            try:
                # Split DOM content into chunks
                dom_chunks = split_dom_content(st.session_state.dom_content)

                # Parse using Together AI
                parsed_result = parse_with_together(dom_chunks, parse_description)

                # Display results
                if parsed_result.strip():
                    st.success("Content parsed successfully!")
                    st.write(parsed_result)
                else:
                    st.warning("No results returned from parsing.")

            except Exception as e:
                st.error(f"Error parsing content: {str(e)}")
                st.info("Please try rephrasing your parsing request or verify your API key configuration.")

        else:
            st.warning("Please describe what you want to parse.")

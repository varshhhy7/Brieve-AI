import os
import asyncio
import streamlit as st
import requests
from bs4 import BeautifulSoup
from pydantic_ai import Agent


os.environ["GROQ_API_KEY"] = "....."


agent = Agent(
    model="groq:llama-3.3-70b-versatile"
)


def fetch_web_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
     
        for script in soup(["script", "style"]):
            script.decompose()
        
       
        text = soup.get_text()
        
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit text length (to avoid token limits but keep more content)
        return text[:15000] if text else "No content found"
        
    except Exception as e:
        raise Exception(f"Failed to fetch content: {str(e)}")

# Async function to summarize content
async def summarize_content(content):
    prompt = f"""
    Analyze and create a comprehensive, detailed summary of the following web content. Structure it professionally:

    Content:
    {content}

    Requirements:
    - Create a detailed **Executive Summary** at the top (2-3 paragraphs)
    - Use clear **section headings** with substantial content under each
    - Include **detailed bullet points** (3-5 points per section, each 1-2 sentences)
    - Cover ALL key concepts, benefits, use cases, technical details, and implications
    - Include specific examples, data, or statistics mentioned
    - Add a **Key Takeaways** section at the end
    - Format everything in **Markdown** with proper headings (##, ###)
    - Make it comprehensive - aim for a thorough analysis, not just a brief overview
    - Include any relevant background context or industry implications
    - Don't skip important details - be thorough and informative

    The summary should be substantial and detailed enough to give someone a complete understanding of the topic without reading the original content.
    """
    
    try:
        result = await agent.run(prompt)
        return result.output if hasattr(result, 'output') else str(result)
    except Exception as e:
        raise Exception(f"Summarization failed: {str(e)}")

# Combined function
async def summarize_url(url):
    status_placeholder = st.empty()
    
    try:
      
        status_placeholder.info("🔄 Fetching web content...")
        content = fetch_web_content(url)
        
        if not content or len(content.strip()) < 100:
            raise Exception("Insufficient content found on the webpage")
        
       
        status_placeholder.info("🧠 Analyzing content and generating detailed summary...")
        summary = await summarize_content(content)
        
        
        status_placeholder.empty()
        return summary
        
    except Exception as e:
        status_placeholder.empty()
        raise Exception(f"Process failed: {str(e)}")


st.set_page_config(page_title="Brieve.AI - Smart Summarizer", layout="wide")
st.title("📄 Brieve.AI - Smart Web Summarizer")
st.markdown("Paste any article URL and get a clean summary with bullet points and section headers.")


url = st.text_input(
    "🔗 Enter article URL", 
    placeholder="Enter the URL you want to summarize (e.g., https://www.example.com/article)",
    help="Paste any web article URL here"
)


if st.button("🧠 Summarize"):
    if url and url.strip():
   
        if not (url.startswith("http://") or url.startswith("https://")):
            st.error("⚠️ Please enter a valid URL starting with http:// or https://")
        else:
            with st.spinner("🔄 Processing..."):
                try:
                  
                    output = asyncio.run(summarize_url(url.strip()))
                    
                    if output:
                        st.success("✅ Detailed summary generated successfully!")
                        st.markdown("---")
                        
                        
                        st.download_button(
                            label="📥 Download Summary",
                            data=output,
                            file_name=f"summary_{url.split('/')[-1][:20]}.md",
                            mime="text/markdown"
                        )
                        
                        st.markdown("### ✨ Comprehensive Summary:")
                        st.markdown(output, unsafe_allow_html=True)
                    else:
                        st.error("⚠️ No summary could be generated.")
                        
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"⚠️ Error: {error_msg}")
                    
                    with st.expander("🔍 Debug Information"):
                        st.code(f"Error details: {error_msg}")
                        st.markdown("**Possible causes:**")
                        if "fetch" in error_msg.lower():
                            st.markdown("- Website is blocking requests or requires authentication")
                            st.markdown("- URL is not accessible or returns no content")
                        elif "groq" in error_msg.lower() or "api" in error_msg.lower():
                            st.markdown("- GROQ API key issue or quota exceeded")
                        elif "timeout" in error_msg.lower():
                            st.markdown("- Request timeout - website is too slow")
                    
                    st.info("💡 Try these solutions:")
                    st.markdown("""
                    1. **Try a different URL**: Some sites block automated requests
                    2. **Use simple articles**: News articles, blogs, Wikipedia work best
                    3. **Check your API key**: Ensure GROQ API key is valid
                    4. **Wait and retry**: If quota exceeded, wait a bit
                    """)
    else:
        st.warning("⚠️ Please enter a valid URL to summarize.")

with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Paste a URL**: Copy any article URL from news sites, blogs, or documentation
    2. **Click Summarize**: The app will fetch content and generate a summary
    3. **Get structured summary**: Receive a clean summary with headings and bullet points
    
    **Works best with**: News articles, blog posts, documentation, Wikipedia pages
    **May not work with**: Sites requiring login, heavily JavaScript-based content, or sites that block bots
    """)


st.sidebar.title("📦 Required Dependencies")
st.sidebar.code("""
pip install streamlit
pip install pydantic-ai
pip install requests
pip install beautifulsoup4
""")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Powered by Groq LLaMA (Fallback Mode - No MCP)</div>", 
    unsafe_allow_html=True
)
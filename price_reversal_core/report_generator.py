import google.generativeai as genai
import os

def generate_report(news_summary: str, primer_content: str, base_prompt: str) -> str:
    """
    Generates a report using Gemini based on news summary and prompts.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found."

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-pro")
    model = genai.GenerativeModel(model_name)

    full_prompt = f"""
    {base_prompt}
    
    ---
    CONTEXT DOCUMENT (Price Reversal Primer):
    {primer_content}
    
    ---
    NEWS SUMMARY:
    {news_summary}
    """
    
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error generating report: {str(e)}"

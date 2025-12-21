import re
import html

def clean_text(text: str) -> str:
    """
    Cleans raw text by removing HTML tags, normalizing whitespace, 
    and unescaping HTML entities.
    """
    if not text:
        return ""
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    # Remove HTML tags using regex
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace (replace multiple spaces/newlines with single space)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

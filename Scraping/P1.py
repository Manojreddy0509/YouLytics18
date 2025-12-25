import re

def get_vid(url):
    """Extract video ID from various YouTube URL formats."""
    if not url:
        return None
        
    patterns = [
        r'(?:v=)([a-zA-Z0-9_-]{11})',      # youtube.com/watch?v=
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})', # youtu.be/
        r'(?:embed/)([a-zA-Z0-9_-]{11})',   # youtube.com/embed/
        r'(?:shorts/)([a-zA-Z0-9_-]{11})'   # youtube.com/shorts/
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
    # Fallback for simple ID
    if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
        
    return None




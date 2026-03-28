import sys
import html2text
from scrapling import Fetcher

def fetch_url(url, max_chars):
    try:
        # Fetcher usage per standard scrapling docs
        page = Fetcher.get(url)
        
        # Selectors
        selectors = ['article', 'main', '.post-content', '[class*="body"]']
        content_html = ""
        
        # In scrapling (similar to parsel), css() returns a SelectorList. We need to extract the raw HTML.
        # Often it's element.get() or element.extract()
        for sel in selectors:
            elements = page.css(sel)
            if elements:
                # Using get() to get the string html
                content_html = elements[0].get() if hasattr(elements[0], 'get') else str(elements[0])
                break
                
        # Fallback
        if not content_html:
            body = page.css('body')
            if body:
                content_html = body[0].get() if hasattr(body[0], 'get') else str(body[0])
            else:
                content_html = page.text if hasattr(page, 'text') else str(page)
                
        # Convert HTML to Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        markdown = h.handle(content_html)
        
        # Truncate
        if max_chars > 0:
            markdown = markdown[:max_chars]
            
        print(markdown)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scrapling_fetch.py <url> [max_chars]")
        sys.exit(1)
        
    url = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    fetch_url(url, max_chars)

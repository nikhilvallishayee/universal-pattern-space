"""
External API interfaces for knowledge ingestion.

Provides interfaces for Wikipedia, web scraping, and content processing.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from html import unescape

logger = logging.getLogger(__name__)


class WikipediaAPI:
    """Wikipedia API interface."""
    
    def __init__(self):
        self.initialized = False
    
    async def initialize(self):
        """Initialize Wikipedia API."""
        logger.info("Initializing Wikipedia API...")
        self.initialized = True
        logger.info("Wikipedia API initialized")
    
    async def shutdown(self):
        """Shutdown Wikipedia API."""
        logger.info("Shutting down Wikipedia API...")
        self.initialized = False
        logger.info("Wikipedia API shutdown complete")
    
    async def get_page_content(self, title: str, language: str = "en") -> Dict[str, Any]:
        """Get Wikipedia page content using the official Wikipedia API."""
        try:
            import httpx
            
            # Use Wikipedia API to get page content
            base_url = f"https://{language}.wikipedia.org/w/api.php"
            
            # First, get page info and content
            params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "extracts|info|pageimages",
                "exintro": False,  # Get full content, not just intro
                "explaintext": True,  # Get plain text, not HTML
                "inprop": "url",
                "piprop": "original",
                "redirects": 1,  # Follow redirects
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # Extract page data
            pages = data.get("query", {}).get("pages", {})
            
            if not pages:
                raise ValueError(f"No Wikipedia page found for title: {title}")
            
            page_id = list(pages.keys())[0]
            page_data = pages[page_id]
            
            if page_id == "-1":
                raise ValueError(f"Wikipedia page not found: {title}")
            
            # Extract content and metadata
            content = page_data.get("extract", "")
            actual_title = page_data.get("title", title)
            page_url = page_data.get("fullurl", f"https://{language}.wikipedia.org/wiki/{title.replace(' ', '_')}")
            
            # Get additional metadata - categories and sections
            sections_params = {
                "action": "parse",
                "format": "json",
                "page": actual_title,
                "prop": "sections",
                "redirects": 1,
            }
            
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    sections_response = await client.get(base_url, params=sections_params)
                    sections_data = sections_response.json()
                    sections = [section.get("line", "") for section in 
                              sections_data.get("parse", {}).get("sections", [])]
            except Exception as e:
                logger.warning(f"Could not fetch sections for {title}: {e}")
                sections = ["Introduction", "Content"]
            
            # Create summary from first paragraph
            summary = ""
            if content:
                paragraphs = content.split("\n\n")
                summary = paragraphs[0] if paragraphs else content[:500] + "..."
            
            result = {
                "title": actual_title,
                "content": content,
                "url": page_url,
                "language": language,
                "summary": summary,
                "sections": sections,
                "word_count": len(content.split()) if content else 0,
                "char_count": len(content) if content else 0,
            }
            
            logger.info(f"Successfully fetched Wikipedia content for '{actual_title}' ({len(content)} chars)")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching Wikipedia content for '{title}': {e}")
            # Fallback to mock data with clear indication it's a fallback
            return {
                "title": title,
                "content": f"[OFFLINE MODE] Unable to fetch real Wikipedia content for: {title}. Network error: {str(e)}",
                "url": f"https://{language}.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "language": language,
                "summary": f"[OFFLINE MODE] Unable to fetch summary for {title}",
                "sections": ["Introduction", "Content", "References"],
                "word_count": 0,
                "char_count": 0,
                "error": str(e),
                "is_fallback": True
            }
        except Exception as e:
            logger.error(f"Error fetching Wikipedia content for '{title}': {e}")
            # Fallback to mock data with clear indication it's a fallback
            return {
                "title": title,
                "content": f"[ERROR] Could not fetch Wikipedia content for: {title}. Error: {str(e)}",
                "url": f"https://{language}.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "language": language,
                "summary": f"[ERROR] Could not fetch summary for {title}",
                "sections": ["Introduction", "Content", "References"],
                "word_count": 0,
                "char_count": 0,
                "error": str(e),
                "is_fallback": True
            }


class WebScraper:
    """Web scraping interface."""
    
    def __init__(self):
        self.initialized = False
    
    async def initialize(self):
        """Initialize web scraper."""
        logger.info("Initializing Web Scraper...")
        self.initialized = True
        logger.info("Web Scraper initialized")
    
    async def shutdown(self):
        """Shutdown web scraper."""
        logger.info("Shutting down Web Scraper...")
        self.initialized = False
        logger.info("Web Scraper shutdown complete")
    
    async def scrape_url(self, url: str, selectors: List[str] = None) -> Dict[str, Any]:
        """Scrape content from a URL using httpx and basic HTML parsing."""
        try:
            import httpx
            from html import unescape
            import re
            
            logger.info(f"Scraping URL: {url}")
            
            # Set up headers to appear as a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text
            
            # Basic HTML parsing without requiring BeautifulSoup
            title = self._extract_title(html_content)
            content = self._extract_text_content(html_content)
            description = self._extract_meta_description(html_content)
            keywords = self._extract_keywords(content)
            
            # Extract basic metadata
            word_count = len(content.split())
            char_count = len(content)
            
            result = {
                "url": url,
                "title": title,
                "content": content,
                "text_content": content,  # Same as content for basic implementation
                "description": description,
                "word_count": word_count,
                "char_count": char_count,
                "metadata": {
                    "description": description,
                    "keywords": keywords,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                }
            }
            
            logger.info(f"Successfully scraped {url}: {word_count} words, {char_count} characters")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping {url}: {e}")
            return {
                "url": url,
                "title": f"[ERROR] Could not access {url}",
                "content": f"[NETWORK ERROR] Unable to scrape content from {url}. HTTP error: {str(e)}",
                "text_content": f"[NETWORK ERROR] Unable to scrape content from {url}.",
                "description": "",
                "word_count": 0,
                "char_count": 0,
                "error": str(e),
                "is_fallback": True,
                "metadata": {
                    "description": f"Error accessing {url}",
                    "keywords": [],
                    "error": str(e)
                }
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "url": url,
                "title": f"[ERROR] Failed to scrape {url}",
                "content": f"[SCRAPING ERROR] Could not extract content from {url}. Error: {str(e)}",
                "text_content": f"[SCRAPING ERROR] Could not extract content from {url}.",
                "description": "",
                "word_count": 0,
                "char_count": 0,
                "error": str(e),
                "is_fallback": True,
                "metadata": {
                    "description": f"Error scraping {url}",
                    "keywords": [],
                    "error": str(e)
                }
            }
    
    def _extract_title(self, html: str) -> str:
        """Extract title from HTML."""
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = unescape(title_match.group(1).strip())
            return re.sub(r'\s+', ' ', title)
        return "Untitled"
    
    def _extract_text_content(self, html: str) -> str:
        """Extract text content from HTML."""
        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Extract content from common content areas
        content_patterns = [
            r'<main[^>]*>(.*?)</main>',
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
        ]
        
        content = ""
        for pattern in content_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            if matches:
                content = ' '.join(matches)
                break
        
        # If no specific content areas found, extract from body
        if not content:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.IGNORECASE | re.DOTALL)
            if body_match:
                content = body_match.group(1)
            else:
                content = html
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Decode HTML entities
        content = unescape(content)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def _extract_meta_description(self, html: str) -> str:
        """Extract meta description from HTML."""
        desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"[^>]*>', html, re.IGNORECASE)
        if desc_match:
            return unescape(desc_match.group(1).strip())
        return ""
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract basic keywords from content."""
        if not content:
            return []
        
        # Simple keyword extraction - get common words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top 10 most common words (excluding very common words)
        stop_words = {'that', 'this', 'with', 'have', 'will', 'been', 'from', 'they', 'know', 'want', 'were', 'there', 'said', 'each', 'which', 'their', 'time', 'would', 'about', 'could', 'other', 'after', 'first', 'well', 'way', 'many', 'must', 'say', 'number', 'part', 'over', 'just', 'like', 'only', 'new', 'more', 'most', 'very', 'also', 'can', 'may', 'use', 'these', 'some', 'what', 'see', 'him', 'two', 'how', 'its', 'who', 'did', 'yes', 'his', 'has', 'had', 'let', 'put', 'too', 'old', 'any', 'day', 'get', 'man', 'own', 'say', 'she', 'may', 'use'}
        
        keywords = [word for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True) 
                   if word not in stop_words and count > 1][:10]
        return keywords


class ContentProcessor:
    """Content processing utilities."""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.,!?;:()-]', '', text)
        return text.strip()
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_content(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split content into chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space
            
            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction - count word frequency
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'
        }
        
        filtered_words = [w for w in words if w not in stop_words]
        
        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def detect_language(self, text: str) -> str:
        """Detect language of text content."""
        # Simple language detection - would use proper library in production
        if any(ord(char) > 127 for char in text):
            return "non-english"
        return "en"


# Global instances
wikipedia_api = WikipediaAPI()
web_scraper = WebScraper()
content_processor = ContentProcessor()
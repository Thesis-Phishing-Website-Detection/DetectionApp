import re
from typing import Optional
from bs4 import BeautifulSoup
from pathlib import Path


class HTMLPreprocessor:
    """
    Preprocesses HTML content for DistilBERT input.
    Removes scripts, styles, and extracts clean visible text.
    """
    
    def __init__(self, max_text_length: int = 512):
        """
        Initialize the preprocessor.
        
        Args:
            max_text_length: Maximum number of characters to keep (approximate token limit)
        """
        self.max_text_length = max_text_length
    
    def clean_html(self, html_content: str) -> str:
        """
        Clean HTML by removing scripts, styles, and extracting visible text.
        
        Args:
            html_content: Raw HTML content
        
        Returns:
            Cleaned text
        """
        try:
            # Try lxml first, fallback to html.parser
            try:
                soup = BeautifulSoup(html_content, 'lxml')
            except Exception:
                soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, str)):
                if isinstance(comment.parent, type(soup)) or comment.parent.name in ['html', 'body']:
                    pass
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            text = self._normalize_whitespace(text)
            
            return text
        
        except Exception as e:
            print(f"✗ Error cleaning HTML: {e}")
            return ""
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Input text
        
        Returns:
            Normalized text
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with single newline
        text = re.sub(r'\n+', '\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def truncate_text(self, text: str) -> str:
        """
        Truncate text to max_text_length characters.
        
        Args:
            text: Input text
        
        Returns:
            Truncated text
        """
        if len(text) > self.max_text_length:
            text = text[:self.max_text_length]
        
        return text
    
    def split_into_sections(self, text: str) -> dict:
        """
        Split text into top, middle, and bottom sections.
        
        Args:
            text: Input text
        
        Returns:
            Dictionary with 'top', 'middle', 'bottom' sections
        """
        if not text:
            return {'top': '', 'middle': '', 'bottom': ''}
        
        length = len(text)
        third = length // 3
        
        return {
            'top': text[:third],
            'middle': text[third:2*third],
            'bottom': text[2*third:]
        }
    
    def preprocess(self, html_content: str) -> dict:
        """
        Full preprocessing pipeline: clean HTML -> normalize -> truncate.
        
        Args:
            html_content: Raw HTML content
        
        Returns:
            Dictionary with 'text' and 'was_truncated' keys
        """
        text = self.clean_html(html_content)
        text = self._normalize_whitespace(text)
        was_truncated = len(text) > self.max_text_length
        text = self.truncate_text(text)
        sections = self.split_into_sections(text)
        return {
            'text': text,
            'was_truncated': was_truncated,
            'sections': sections
        }
    
    def preprocess_file(self, file_path: str) -> str:
        """
        Load HTML file and preprocess.
        
        Args:
            file_path: Path to HTML file
        
        Returns:
            Preprocessed text
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            return self.preprocess(html_content)
        
        except Exception as e:
            print(f"✗ Error preprocessing file {file_path}: {e}")
            return ""


def preprocess_batch(file_paths: list, max_workers: int = 4) -> list:
    """
    Preprocess multiple HTML files in parallel.
    
    Args:
        file_paths: List of file paths to process
        max_workers: Number of parallel workers
    
    Returns:
        List of preprocessed texts
    """
    preprocessor = HTMLPreprocessor()
    results = []
    
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(preprocessor.preprocess_file, fp): fp for fp in file_paths}
        
        from tqdm import tqdm
        for future in tqdm(futures, total=len(futures), desc="Preprocessing HTML"):
            results.append(future.result())
    
    return results


if __name__ == "__main__":
    # Example usage
    preprocessor = HTMLPreprocessor(max_text_length=512)
    
    # Test with a sample HTML file
    sample_files = list(Path("Mendeley Data/dataset").rglob("*.html"))[:5]
    
    print(f"✓ Testing preprocessing on {len(sample_files)} sample files...\n")
    
    for file_path in sample_files:
        print(f"File: {file_path.name}")
        text = preprocessor.preprocess_file(str(file_path))
        print(f"  Original size: {file_path.stat().st_size} bytes")
        print(f"  Text length: {len(text)} chars")
        print(f"  Preview: {text[:100]}...\n")

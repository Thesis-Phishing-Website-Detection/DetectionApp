import logging
import os
from typing import Tuple
from langdetect import detect, LangDetectException, detect_langs
from bs4 import BeautifulSoup
import deepl

logger = logging.getLogger(__name__)


class TextTranslator:
    """
    Translates non-English text to English using DeepL API.
    Detects language automatically and skips translation for English.
    """
    
    def __init__(self):
        """Initialize translator with DeepL API key."""
        api_key = os.getenv('DEEPL_API_KEY')
        if not api_key:
            logger.warning("DEEPL_API_KEY not found in .env, translation will be skipped")
            self.translator = None
        else:
            try:
                self.translator = deepl.Translator(api_key)
                logger.info("✓ DeepL translator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize DeepL: {e}")
                self.translator = None
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of text.
        
        Args:
            text: Input text
        
        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            # Use first 500 chars for detection (faster)
            sample_text = text[:500] if len(text) > 500 else text
            lang = detect(sample_text)
            return lang, 0.95
        except LangDetectException:
            logger.warning("Could not detect language, assuming English")
            return 'en', 0.5
        except Exception as e:
            logger.warning(f"Language detection error: {e}, assuming English")
            return 'en', 0.5
    
    def get_translator(self, src_lang: str):
        """
        Verify DeepL translator is available.
        
        Args:
            src_lang: Source language code (for logging)
        
        Returns:
            DeepL translator object or None
        """
        if self.translator is None:
            logger.warning("DeepL translator not available")
            return None
        return self.translator
    
    def translate(self, text: str, max_length: int = 2048) -> Tuple[str, str, bool]:
        """
        Translate text to English if needed using DeepL API.
        
        Args:
            text: Input text (can be HTML)
            max_length: Maximum characters to translate (for efficiency)
        
        Returns:
            Tuple of (translated_text, language_code, was_translated)
        """
        if not text or len(text) < 10:
            return text, 'en', False
        
        # Extract text from HTML for language detection
        text_for_detection = self._extract_text_from_html(text)
        if not text_for_detection or len(text_for_detection) < 10:
            return text, 'en', False
        
        # Detect language on extracted text only (not HTML markup)
        lang, confidence = self.detect_language(text_for_detection)
        logger.info(f"Detected language: {lang} (confidence: {confidence:.2f})")
        
        # Skip if English
        if lang == 'en':
            logger.info("Text is already in English, skipping translation")
            return text, lang, False
        
        # Check if DeepL is available
        if self.translator is None:
            logger.warning("DeepL translator not available, using original text")
            return text, lang, False
        
        # Prepare text for translation
        text_to_translate = text_for_detection[:max_length] if len(text_for_detection) > max_length else text_for_detection
        
        try:
            logger.info(f"Translating from {lang} to English via DeepL...")
            
            # Map language codes to DeepL language codes
            lang_map = {
                'ar': 'AR',  # Arabic
                'bg': 'BG',  # Bulgarian
                'cs': 'CS',  # Czech
                'cy': 'CY',  # Welsh
                'da': 'DA',  # Danish
                'de': 'DE',  # German
                'el': 'EL',  # Greek
                'en': 'EN',  # English
                'es': 'ES',  # Spanish
                'et': 'ET',  # Estonian
                'fi': 'FI',  # Finnish
                'fr': 'FR',  # French
                'hu': 'HU',  # Hungarian
                'id': 'ID',  # Indonesian
                'it': 'IT',  # Italian
                'ja': 'JA',  # Japanese
                'ko': 'KO',  # Korean
                'lt': 'LT',  # Lithuanian
                'lv': 'LV',  # Latvian
                'nb': 'NB',  # Norwegian
                'nl': 'NL',  # Dutch
                'pl': 'PL',  # Polish
                'pt': 'PT',  # Portuguese
                'ro': 'RO',  # Romanian
                'ru': 'RU',  # Russian
                'sk': 'SK',  # Slovak
                'sl': 'SL',  # Slovenian
                'sv': 'SV',  # Swedish
                'tr': 'TR',  # Turkish
                'uk': 'UK',  # Ukrainian
                'zh': 'ZH',  # Chinese
            }
            
            source_lang = lang_map.get(lang, lang.upper())
            
            # Call DeepL API (use EN-US or EN-GB instead of generic EN)
            result = self.translator.translate_text(
                text_to_translate,
                target_lang='EN-US',
                source_lang=source_lang
            )
            
            translated_text = result.text
            
            logger.info(f"✓ Translation complete ({lang} → en)")
            logger.info(f"  Original length: {len(text_to_translate)} chars")
            logger.info(f"  Translated length: {len(translated_text)} chars")
            
            return translated_text, lang, True
        
        except Exception as e:
            logger.error(f"DeepL translation error: {e}, using original text")
            return text, lang, False
    
    def _extract_text_from_html(self, html: str) -> str:
        """
        Extract visible text from HTML for accurate language detection.
        
        Args:
            html: Raw HTML content
        
        Returns:
            Extracted text without HTML markup
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style tags
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text[:5000]  # Limit to first 5000 chars for detection
        except Exception as e:
            logger.warning(f"Error extracting text from HTML: {e}, using first 2048 chars")
            return html[:2048]

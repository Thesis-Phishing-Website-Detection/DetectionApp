"""
Main CLI entry point for website phishing detection testing.
"""
import argparse
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path to import preprocess module
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from scraper import ScraperAPIClient
from scraper.apify_scraper import fetch_website_apify
from preprocess import HTMLPreprocessor
from translator import TextTranslator
from model_handler import PhishingModelHandler
from dashboard_generator import DashboardGenerator
from crypto_gambling_detector import CryptoGamblingDetector
from pattern_detector import PatternDetector

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / '.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_model_path():
    """Get path to the model directory."""
    # Navigate from websitedetectiontest back to root, then to models/
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    model_path = project_root / 'models' / 'distilbert_phishing_model'
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}\n"
            f"Expected model directory: {model_path}"
        )
    
    return str(model_path)


def setup_results_dir():
    """Get path to results directory."""
    current_dir = Path(__file__).parent
    results_dir = current_dir / 'results'
    return str(results_dir)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Test phishing detection on live websites using ScraperAPI'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help='Website URL to analyze (e.g., https://example.com)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='ScraperAPI key (or set SCRAPER_API_KEY env var)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--locale',
        type=str,
        default='en-US',
        help='Browser locale for ScraperAPI (default: en-US for English)'
    )
    
    parser.add_argument(
        '--render',
        action='store_true',
        help='Enable JavaScript rendering via ScraperAPI (slower, use for single-page apps)'
    )
    
    parser.add_argument(
        '--use-apify',
        action='store_true',
        help='Use Apify API instead of ScraperAPI (supports multi-page crawling)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=5,
        help='Max pages to crawl when using Apify (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key based on which service to use
    if args.use_apify:
        api_key = os.environ.get('APIFY_API_KEY')
        if not api_key:
            logger.error("Apify key required. Set APIFY_API_KEY env var")
            sys.exit(1)
        logger.info("Using Apify API for scraping")
    else:
        api_key = args.api_key or os.environ.get('SCRAPER_API_KEY')
        if not api_key:
            logger.error("ScraperAPI key required. Provide via --api-key or SCRAPER_API_KEY env var")
            sys.exit(1)
        logger.info("Using ScraperAPI for scraping")
    
    try:
        logger.info("=" * 70)
        logger.info("Phishing Website Detection Test")
        logger.info("=" * 70)
        
        # Step 1: Fetch website
        logger.info("\n[Step 1/5] Fetching website content...")
        
        if args.use_apify:
            # Use Apify API
            raw_html = fetch_website_apify(args.url, api_key, max_pages=args.max_pages, timeout=args.timeout)
        else:
            # Use ScraperAPI
            scraper = ScraperAPIClient(api_key)
            # Increase timeout if rendering is enabled (rendering takes longer)
            timeout = args.timeout * 2 if args.render else args.timeout
            raw_html = scraper.fetch_website(args.url, timeout=timeout, locale=args.locale, render=args.render)
        if not raw_html:
            logger.error("Failed to fetch website content")
            sys.exit(1)
        logger.info(f"✓ Fetched {len(raw_html)} bytes")
        
        # Step 1.5: Translate to English if needed
        logger.info("\n[Step 1.5/5] Detecting language and translating if needed...")
        translator = TextTranslator()
        translated_html, detected_lang, was_translated = translator.translate(raw_html)
        if was_translated:
            logger.info(f"✓ Translated from {detected_lang} to English")
            raw_html = translated_html  # Use translated content
        else:
            logger.info(f"✓ Content is in {detected_lang} (no translation needed)")
        
        # Step 2: Process HTML
        logger.info("\n[Step 2/5.5] Processing and cleaning HTML...")
        # Extract up to 2048 characters (4x the model limit for better context)
        preprocessor = HTMLPreprocessor(max_text_length=2048)
        preprocess_result = preprocessor.preprocess(raw_html)
        cleaned_text = preprocess_result['text']
        logger.info(f"✓ Cleaned text: {len(cleaned_text)} characters")
        
        # Create processor result dict for compatibility with dashboard generator
        processor_result = {
            'cleaned_text': cleaned_text,
            'was_truncated': preprocess_result['was_truncated'],
            'sections': preprocess_result.get('sections', {}),
            'preprocessing_steps': ['HTML cleaning', 'Text extraction', 'Normalization']
        }
        
        # Step 3: Load model
        logger.info("\n[Step 3/5.5] Loading model...")
        model_path = setup_model_path()
        model_handler = PhishingModelHandler(model_path)
        logger.info("✓ Model loaded")
        
        # Step 4: Make prediction
        logger.info("\n[Step 4/6] Running model prediction...")
        prediction_result = model_handler.predict(cleaned_text, include_explanation=True)
        
        # Analyze each section (top, middle, bottom) with weighted predictions
        logger.info("\n[Step 4.1/6] Running weighted section analysis...")
        sections_list = []
        sections = processor_result.get('sections', {})
        for section_name, section_text in sections.items():
            if section_text and len(section_text) > 10:  # Only analyze if section has content
                sections_list.append({'name': section_name, 'text': section_text})
        
        # Use weighted aggregation: bottom section (conversion) gets higher weight
        if sections_list:
            weighted_result = model_handler.predict_multiple_sections(
                sections_list,
                use_weighted_average=True,
                section_weights={'top': 0.2, 'middle': 0.3, 'bottom': 0.5}
            )
            prediction_result['weighted_predictions'] = weighted_result
            prediction_result['section_predictions'] = weighted_result['section_predictions']
            
            logger.info(f"  Weighted Result: {weighted_result['aggregate_predicted_label']}")
            logger.info(f"  - Phishing: {weighted_result['aggregate_phishing_probability']:.2%}")
            logger.info(f"  - Legitimate: {weighted_result['aggregate_legitimate_probability']:.2%}")
            logger.info(f"  - Confidence: {weighted_result['aggregate_confidence']:.2%}")
        else:
            logger.info("  No sections available for weighted analysis")
        
        logger.info(f"✓ Full Document Prediction: {prediction_result['predicted_label']}")
        logger.info(f"  - Phishing: {prediction_result['phishing_probability']:.2%}")
        logger.info(f"  - Legitimate: {prediction_result['legitimate_probability']:.2%}")
        logger.info(f"  - Confidence: {prediction_result['confidence']:.2%}")
        
        # Step 4.2: Run pattern detection for scam indicators
        logger.info("\n[Step 4.2/6] Running pattern detection for scam indicators...")
        pattern_results = PatternDetector.detect_patterns(cleaned_text)
        prediction_result['pattern_detection'] = pattern_results
        
        # Log pattern detection results
        logger.info(f"  Pattern Detection Risk Level: {pattern_results['risk_level']}")
        logger.info(f"  - Earning Claims: {len(pattern_results['earning_claims'])}")
        logger.info(f"  - Testimonials: {len(pattern_results['testimonials'])}")
        logger.info(f"  - Urgency Tactics: {len(pattern_results['urgency_tactics'])}")
        logger.info(f"  - Fake Legitimacy: {len(pattern_results['fake_legitimacy'])}")
        logger.info(f"  - Testimonial Clustering: {pattern_results['testimonial_clustering']['testimonial_count']} testimonials")
        
        if pattern_results['flagged']:
            logger.warning(f"🚨 FLAGGED - Potential scam detected by pattern analysis!")
        
        # Step 4.3: Combine ML and pattern detection
        logger.info("\n[Step 4.3/6] Combining ML and pattern detection results...")
        
        # If ML and patterns both indicate phishing, confidence is very high
        # If only one indicates phishing, boost confidence
        ml_predicts_phishing = prediction_result['predicted_label'] == 'Phishing'
        patterns_flag_scam = pattern_results['flagged']
        
        final_assessment = {
            'ml_prediction': prediction_result['predicted_label'],
            'ml_confidence': prediction_result['confidence'],
            'pattern_risk': pattern_results['risk_level'],
            'pattern_risk_score': pattern_results['risk_score'],
            'combined_recommendation': None,
            'boosted_confidence': prediction_result['confidence'],
        }
        
        if ml_predicts_phishing and patterns_flag_scam:
            final_assessment['combined_recommendation'] = 'Phishing'
            final_assessment['boosted_confidence'] = min(1.0, prediction_result['confidence'] + 0.15)
            logger.warning("⚠️  STRONG PHISHING INDICATOR - Both ML and patterns detect phishing")
        elif patterns_flag_scam and not ml_predicts_phishing:
            final_assessment['combined_recommendation'] = 'Likely Phishing (Pattern-based)'
            final_assessment['boosted_confidence'] = min(1.0, prediction_result['confidence'] + 0.25)
            logger.warning("⚠️  PATTERN-BASED PHISHING - Scam patterns detected despite ML classification")
        elif ml_predicts_phishing and not patterns_flag_scam:
            final_assessment['combined_recommendation'] = 'Likely Phishing (ML-based)'
            final_assessment['boosted_confidence'] = prediction_result['confidence']
            logger.warning("⚠️  ML-BASED PHISHING - Model confidence but no strong pattern match")
        else:
            final_assessment['combined_recommendation'] = prediction_result['predicted_label']
            final_assessment['boosted_confidence'] = prediction_result['confidence']
        
        prediction_result['final_assessment'] = final_assessment
        
        # Step 5: Run crypto/gambling detection
        logger.info("\n[Step 5/6] Running crypto/gambling phishing detection...")
        crypto_gambling_result = CryptoGamblingDetector.detect(cleaned_text, args.url)
        prediction_result['crypto_gambling_detection'] = crypto_gambling_result
        
        if crypto_gambling_result['crypto_phishing']['detected']:
            logger.warning(f"⚠️  CRYPTO PHISHING DETECTED (confidence: {crypto_gambling_result['crypto_phishing']['details']['confidence']:.1f}%)")
            logger.warning(f"   Keywords found: {len(crypto_gambling_result['crypto_phishing']['details']['detected_keywords'])}")
            logger.warning(f"   Risk factors: {len(crypto_gambling_result['crypto_phishing']['details']['risk_factors'])}")
        
        if crypto_gambling_result['gambling']['detected']:
            logger.warning(f"⚠️  GAMBLING WEBSITE DETECTED (confidence: {crypto_gambling_result['gambling']['details']['confidence']:.1f}%)")
            logger.warning(f"   Type: {', '.join(crypto_gambling_result['gambling']['details']['gambling_type'])}")
            logger.warning(f"   Keywords found: {len(crypto_gambling_result['gambling']['details']['detected_keywords'])}")
        
        # Step 6: Generate dashboard
        logger.info("\n[Step 6/6] Generating interactive dashboard with side-by-side comparison...")
        results_dir = setup_results_dir()
        dashboard_path = DashboardGenerator.generate_dashboard(
            args.url,
            raw_html,
            processor_result,
            prediction_result,
            results_dir
        )
        logger.info(f"✓ Dashboard generated")
        
        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("ANALYSIS COMPLETE")
        logger.info("=" * 70)
        logger.info(f"URL: {args.url}")
        
        # Display final assessment
        final = prediction_result.get('final_assessment', {})
        logger.info(f"\n📊 FINAL ASSESSMENT:")
        logger.info(f"  ML Model Prediction: {final['ml_prediction']} ({final['ml_confidence']:.2%})")
        logger.info(f"  Pattern Detection Risk: {final['pattern_risk']} ({final['pattern_risk_score']:.2%})")
        logger.info(f"  Combined Recommendation: {final['combined_recommendation']}")
        logger.info(f"  Boosted Confidence: {final['boosted_confidence']:.2%}")
        
        # Display pattern details
        patterns = prediction_result.get('pattern_detection', {})
        if patterns.get('flagged'):
            logger.warning(f"\n🚨 SCAM INDICATORS DETECTED:")
            report = PatternDetector.get_pattern_report(patterns)
            for line in report.split('\n'):
                logger.warning(f"  {line}")
        
        # Display weighted section analysis if available
        weighted = prediction_result.get('weighted_predictions', {})
        if weighted:
            logger.info(f"\n📍 WEIGHTED SECTION ANALYSIS:")
            logger.info(f"  Aggregation Method: {weighted['aggregation_method']}")
            logger.info(f"  Prediction: {weighted['aggregate_predicted_label']} ({weighted['aggregate_confidence']:.2%})")
            logger.info(f"  Section Details:")
            for section in weighted['section_predictions']:
                logger.info(f"    • {section['section_name'].upper()}: {section['predicted_label']} "
                           f"(weight: {section['weight']:.0%}, confidence: {section['confidence']:.2%})")
        
        logger.info(f"\nDashboard saved to:")
        logger.info(f"  {dashboard_path}")
        logger.info(f"\nOpen the HTML file in your browser to view detailed analysis.")
        logger.info("=" * 70)
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

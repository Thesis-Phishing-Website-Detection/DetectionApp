"""Test phishing detection on localtunnel content via direct HTTP request"""
import requests
import sys
from pathlib import Path
sys.path.insert(0, '.')

# Fetch with direct request (bypasses localtunnel warning)
print('Fetching with direct request (curl User-Agent)...')
r = requests.get('https://rotten-mice-repeat.loca.lt/', headers={'User-Agent': 'curl/7.64.1'}, timeout=30)
print(f'Fetched: {len(r.text)} bytes\n')

# Now process and predict
from processor import ContentProcessor
from model_handler import PhishingModelHandler

print('Processing HTML...')
processed = ContentProcessor.process_html(r.text)
print(f'Extracted text: {len(processed["cleaned_text"])} chars\n')

# Setup model
print('Loading model...')
current_dir = Path(__file__).parent
project_root = current_dir.parent
model_path = project_root / 'models' / 'distilbert_phishing_model'
model_handler = PhishingModelHandler(str(model_path))
print(f'Model loaded\n')

print('Running prediction...')
result = model_handler.predict_multiple_sections(processed['sections'])
print(f'\nPrediction Result:')
print(f'  Overall Label: {result.get("aggregate_predicted_label", "unknown")}')
print(f'  Phishing Probability: {result.get("aggregate_phishing_probability", 0):.2%}')
print(f'  Legitimate Probability: {result.get("aggregate_legitimate_probability", 0):.2%}')
print(f'  Confidence: {result.get("aggregate_confidence", 0):.2%}')
print(f'\nSections analyzed: {result.get("section_count", 0)}')

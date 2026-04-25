"""Analyze content extracted from bithash-fidelity.vip to understand misclassification"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from scraper.apify_scraper import fetch_website_apify
from processor import ContentProcessor
import os

# Load API key
api_key = os.getenv('APIFY_API_KEY')
if not api_key:
    print("ERROR: APIFY_API_KEY not set")
    sys.exit(1)

url = "https://bithash-fidelity.vip/"

# Fetch
print(f"Fetching {url}...")
html = fetch_website_apify(url, api_key, max_pages=1)
print(f"✓ Fetched: {len(html)} bytes\n")

# Process
processed = ContentProcessor.process_html(html)
print("=" * 70)
print("EXTRACTED TEXT SECTIONS")
print("=" * 70)

for section in processed['sections']:
    print(f"\n[{section['name'].upper()}]")
    print(f"Size: {len(section['text'])} chars")
    print("-" * 70)
    print(section['text'][:500] + ("..." if len(section['text']) > 500 else ""))
    print()

print("=" * 70)
print("SUSPICIOUS KEYWORDS ANALYSIS")
print("=" * 70)

full_text = processed['cleaned_text'].lower()
suspicious_keywords = [
    'bitcoin', 'crypto', 'wallet', 'private key', 'seed phrase',
    'deposit', 'withdraw', 'invest', 'mining', 'hash rate',
    'verify', 'confirm', 'authenticate', 'login', 'password',
    'wallet address', 'transaction', 'fee', 'profit',
    'claim', 'bonus', 'reward', 'urgent', 'limited time'
]

print(f"\nSearching for {len(suspicious_keywords)} suspicious keywords...")
found_keywords = {}
for keyword in suspicious_keywords:
    count = full_text.count(keyword)
    if count > 0:
        found_keywords[keyword] = count

if found_keywords:
    print("\nFound suspicious keywords:")
    for keyword, count in sorted(found_keywords.items(), key=lambda x: x[1], reverse=True):
        print(f"  • '{keyword}': {count} times")
else:
    print("No suspicious keywords found!")

print(f"\nTotal content analysis:")
print(f"  - Full text length: {len(processed['cleaned_text'])} chars")
print(f"  - Number of sections: {len(processed['sections'])}")

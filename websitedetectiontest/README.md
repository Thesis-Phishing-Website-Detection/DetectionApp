# Website Phishing Detection Test Tool

A CLI tool to test the AI Phishing Website Detection model on **live websites** in real-time using ScraperAPI. The tool extracts website content, processes it through the same pipeline as the training data, generates predictions with confidence scores, and visualizes everything in an interactive HTML dashboard with attention-based token importance explanations.

## Features

✅ **Live Website Fetching** — Uses ScraperAPI to extract content from any website
✅ **Full Processing Pipeline** — Applies the same HTML cleaning, normalization, and truncation as training data
✅ **Model Inference** — Runs the pretrained DistilBERT model with CPU support
✅ **Attention-Based Explanations** — Shows which tokens most influenced the prediction
✅ **Interactive Dashboard** — Beautiful HTML report with all preprocessing steps, tokenization details, and results
✅ **Detailed Logging** — Clear console output for each step

## Quick Start

### 1. Setup

From the `websitedetectiontest` directory:

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your ScraperAPI key
copy .env.example .env
# Edit .env and replace with your actual ScraperAPI key
```

Get your ScraperAPI key from: https://www.scraperapi.com (free tier available)

### 2. Run Analysis

```bash
# Analyze a website
python main.py --url https://example.com

# Or provide API key directly
python main.py --url https://example.com --api-key YOUR_API_KEY
```

### 3. View Results

The tool generates an HTML dashboard in `results/` folder:
- **Filename**: `<url_hash>_dashboard.html`
- **Location**: `websitedetectiontest/results/`
- Open the HTML file in any browser

## Usage

### Basic Usage

```bash
python main.py --url https://example.com
```

### With API Key

```bash
python main.py --url https://example.com --api-key 7c16bff05342c974e711f0385639c640
```

### Custom Timeout

```bash
python main.py --url https://example.com --timeout 60
```

### Environment Variable

```bash
# Set environment variable (Windows)
set SCRAPER_API_KEY=your_api_key_here
python main.py --url https://example.com

# Or Linux/Mac
export SCRAPER_API_KEY=your_api_key_here
python main.py --url https://example.com
```

## Output Example

### Console Output

```
======================================================================
Phishing Website Detection Test
======================================================================

[Step 1/5] Fetching website content...
✓ Fetched 45,230 bytes

[Step 2/5] Processing and cleaning HTML...
✓ Cleaned text: 512 characters

[Step 3/5] Loading model...
✓ Model loaded

[Step 4/5] Running model prediction...
✓ Prediction: Phishing
  - Phishing: 87.50%
  - Legitimate: 12.50%
  - Confidence: 87.50%

[Step 5/5] Generating interactive dashboard...
✓ Dashboard generated

======================================================================
ANALYSIS COMPLETE
======================================================================
URL: https://example.com
Result: Phishing
Confidence: 87.50%

Dashboard saved to:
  c:\Users\tgen1\Documents\Codes\AIPhishingWebsiteDetection\websitedetectiontest\results\a1b2c3d4_dashboard.html

Open the HTML file in your browser to view detailed analysis.
======================================================================
```

### HTML Dashboard Sections

The generated dashboard contains:

1. **Prediction Result** — Color-coded result (Red=Phishing, Green=Legitimate) with confidence scores
2. **Input URL** — The website analyzed
3. **Raw HTML Preview** — First 500 characters of the fetched HTML
4. **Preprocessing Steps** — Detailed log of all cleaning operations
5. **Cleaned Text** — Final text sent to the model (with truncation warning if applicable)
6. **Tokenization Details** — Token count and preview of first 50 tokens
7. **Important Tokens** — Bar chart of tokens with highest attention weights (attribution)

## File Structure

```
websitedetectiontest/
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
├── processor.py              # HTML processing pipeline
├── model_handler.py          # Model loading & inference
├── dashboard_generator.py    # HTML dashboard creation
├── scraper/
│   ├── __init__.py
│   └── scraper.py           # ScraperAPI wrapper
├── results/                  # Output dashboards (generated)
└── dashboard/               # Dashboard templates (for future use)
```

## How It Works

### 1. Website Fetching (ScraperAPI)
- Uses ScraperAPI to fetch raw HTML from the URL
- Handles network errors gracefully
- Returns raw HTML content

### 2. Preprocessing Pipeline
- **Clean HTML**: Uses BeautifulSoup to remove `<script>`, `<style>` tags and extract visible text
- **Normalize Whitespace**: Removes multiple spaces/newlines, strips leading/trailing whitespace
- **Truncate**: Limits text to ~512 characters (model's token limit)

### 3. Model Inference
- **Loads**: DistilBERT model from `../models/distilbert_phishing_model/`
- **Tokenizes**: Converts cleaned text to 512 tokens (pads with special tokens)
- **Predicts**: Outputs probabilities for Legitimate (class 0) vs Phishing (class 1)
- **Attribution**: Extracts attention weights to identify important tokens

### 4. Dashboard Generation
- Creates interactive HTML with embedded CSS/JavaScript
- Color-coded results (red for phishing, green for legitimate)
- Shows preprocessing steps, tokens, and importance scores
- No external dependencies needed (fully self-contained HTML)

## Model Details

- **Model**: DistilBERT for binary classification
- **Checkpoint**: `models/distilbert_phishing_model/`
- **Training Accuracy**: ~91.5%
- **Test ROC-AUC**: ~96.85%
- **Input**: Text up to 512 tokens
- **Output**: Probabilities for 2 classes (Legitimate, Phishing)

## Troubleshooting

### "API key is required"
**Solution**: Set `SCRAPER_API_KEY` environment variable or provide `--api-key` argument

```bash
python main.py --url https://example.com --api-key YOUR_KEY
```

### "Model not found"
**Solution**: Ensure you're running from the `websitedetectiontest` directory and the model exists at `../models/distilbert_phishing_model/`

```bash
# From websitedetectiontest folder:
python main.py --url https://example.com
```

### "Connection timeout"
**Solution**: Increase timeout value (default: 30 seconds)

```bash
python main.py --url https://example.com --timeout 60
```

### "Empty response from ScraperAPI"
**Solution**: Website may be blocking API calls or have issues. Try a different URL

### "CUDA error" or GPU issues
**Solution**: Tool automatically uses CPU. If you see GPU errors, ignore them—inference will use CPU instead

## Limitations

- **Single URL per run** — Process one website at a time (not batch)
- **No result caching** — Each run fetches fresh content from the internet
- **No retry logic** — Fails immediately if ScraperAPI call fails
- **Text truncation** — Websites larger than 512 tokens are truncated
- **CPU only** — Due to RTX 5060 GPU compatibility limitations

## Future Enhancements

- Batch processing multiple URLs
- Result caching to save API calls
- Retry logic with exponential backoff
- Web API server interface
- Batch CSV import/export
- Historical result tracking
- Model fine-tuning on custom datasets

## API Key

Get your free ScraperAPI key:
1. Visit https://www.scraperapi.com
2. Sign up (free tier includes ~1,000 requests/month)
3. Copy your API key from the dashboard
4. Set it in `.env` or pass via `--api-key`

## Dependencies

- `torch` — Deep learning framework
- `transformers` — HuggingFace transformers library
- `requests` — HTTP client for ScraperAPI
- `beautifulsoup4` — HTML parsing
- `jinja2` — HTML template rendering
- `python-dotenv` — Environment variable loading

## License

Same as parent project (AI Phishing Website Detection)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your ScraperAPI key is valid
3. Ensure model checkpoint exists at `../models/distilbert_phishing_model/`
4. Check console logs for detailed error messages

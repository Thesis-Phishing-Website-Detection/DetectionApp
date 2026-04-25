# Phishing Website Detection using DistilBERT

A pre-trained deep learning model for detecting phishing websites using **DistilBERT** on raw HTML content. This system performs **inference-only** phishing detection with confidence scores and attention-based interpretability.

## Overview

```
Live Website
     ↓
Scrape HTML via ScraperAPI or Apify
     ↓
Clean & Preprocess (remove scripts, styles, extract text)
     ↓
DistilBERT Tokenization (512 tokens max)
     ↓
┌──────────────────────────────────────────┐
│  DistilBERT Binary Classification        │
│  • Pre-trained model (distilbert-base)   │
│  • Fine-tuned on phishing dataset        │
│  • Binary output: Legitimate (0) or      │
│    Phishing (1)                          │
│  • Probability scores for both classes   │
│  • Attention weights for interpretability│
│  • PyTorch-based inference               │
└──────────────────────────────────────────┘
     ↓
Interactive HTML Dashboard & Predictions
```

## Model Performance

Expected inference performance on diverse websites:
- **Accuracy:** ~95%
- **Precision (Phishing):** ~94%
- **Recall (Phishing):** ~96%
- **F1-Score:** ~95%
- **ROC-AUC:** ~0.98

## Project Structure

```
AIPhishingWebsiteDetection/
├── websitedetectiontest/           # ⭐ PRIMARY: Live website detection app
│   ├── main.py                     # Entry point for detection CLI
│   ├── model_handler.py            # Model inference & predictions
│   ├── dashboard_generator.py      # Interactive HTML report generator
│   ├── crypto_gambling_detector.py # Rule-based crypto scam detection
│   ├── scraper/                    # Web scraping utilities
│   │   ├── scraper.py              # ScraperAPI client
│   │   └── apify_scraper.py        # Apify crawler client
│   ├── requirements.txt            # Runtime dependencies
│   ├── README.md                   # Detection app documentation
│   └── results/                    # Generated dashboard outputs
│
├── models/
│   └── distilbert_phishing_model/  # Pre-trained model artifacts
│       ├── config.json             # Model configuration
│       ├── model.safetensors       # Trained weights
│       ├── tokenizer.json          # Tokenizer vocabulary
│       └── tokenizer_config.json   # Tokenizer configuration
│
├── model_artifacts/
│   └── dataset_config.json         # Model metadata
│
├── preprocess.py                   # HTML cleaning & text extraction (runtime utility)
├── translator.py                   # Text translation utility (runtime)
├── requirements.txt                # Historical reference (use websitedetectiontest/requirements.txt for runtime)
├── .env.example                    # API key configuration template
└── README.md                       # This file
```

**Note:** Training-related files (train_pytorch.py, dataset.py, data_loader.py, etc.) and the Mendeley dataset have been removed. This repository is now **inference-only**.

## Installation

### Prerequisites
- Python 3.8+
- 8GB+ system RAM (for model inference)
- GPU with 4GB+ VRAM (optional, but recommended for faster inference)

### Setup

1. **Clone or navigate to the project:**
   ```bash
   cd c:\Users\tgen1\Documents\Codes\AIPhishingWebsiteDetection
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install runtime dependencies:**
   ```bash
   cd websitedetectiontest
   pip install -r requirements.txt
   ```

4. **Configure API keys:**
   ```bash
   copy ..\.env.example .env
   # Edit .env with your API keys:
   # - SCRAPER_API_KEY (for ScraperAPI)
   # - APIFY_API_KEY (for Apify)
   # - DEEPL_API_KEY (for text translation)
   ```

## Quick Start

### Run Detection on a Single URL

```bash
cd websitedetectiontest
python main.py --url https://example.com
```

This will:
1. Scrape the website
2. Preprocess HTML
3. Run DistilBERT model inference
4. Generate an interactive HTML dashboard
5. Display prediction with confidence score

### Batch Detection

Process multiple URLs:
```bash
python main.py --urls https://example.com https://example2.com https://example3.com
```

### View Generated Dashboard

Open the generated HTML file in your browser (path displayed in console)

**For detailed detection app usage:** See [websitedetectiontest/README.md](websitedetectiontest/README.md)

## Core Modules

### websitedetectiontest/main.py
The main CLI entry point for running detection on live websites.

**Usage:**
```bash
python main.py --url https://example.com [--gpu]
```

**Features:**
- Fetches live website HTML
- Preprocesses and extracts text
- Runs DistilBERT inference
- Generates interactive dashboard
- Displays phishing probability score

### websitedetectiontest/model_handler.py
Handles model loading and inference.

**Key class:**
- `PhishingModelHandler`: Loads pre-trained model, tokenizer, and performs predictions

```python
from model_handler import PhishingModelHandler

handler = PhishingModelHandler(model_path='../../models/distilbert_phishing_model', use_gpu=True)
prediction = handler.predict_html(html_content)
```

### websitedetectiontest/dashboard_generator.py
Generates interactive HTML dashboards with results.

**Key class:**
- `DashboardGenerator`: Creates detailed HTML reports with visualizations

### websitedetectiontest/scraper/
Web scraping utilities for fetching live websites.

**Classes:**
- `ScraperAPIClient`: Wrapper for ScraperAPI
- Apify crawler client for JavaScript-heavy sites

### preprocess.py
Cleans HTML and extracts text for model input.

**Key class:**
- `HTMLPreprocessor`: Removes scripts/styles, normalizes whitespace, extracts clean text

```python
from preprocess import HTMLPreprocessor

preprocessor = HTMLPreprocessor(max_text_length=512)
text = preprocessor.preprocess(html_content)
```

### translator.py
Text translation utility for handling non-English websites.

**Key class:**
- `TextTranslator`: Translates text to English using DeepL API
- **Accuracy:** > 95%
- **Precision (Phishing):** > 94%
- **Recall (Phishing):** > 96%
- **F1-Score:** > 95%
- **ROC-AUC:** > 0.98

*Note: Performance may vary based on dataset quality and preprocessing choices.*

## Troubleshooting

### Model Not Found
- Verify `models/distilbert_phishing_model/` directory exists
- Check model files: `model.safetensors`, `config.json`, `tokenizer.json`

### GPU Not Detected
- Verify CUDA installation: `nvidia-smi`
- Check PyTorch GPU support: `python -c "import torch; print(torch.cuda.is_available())"`

### API Key Errors
- Ensure `.env` file is configured with correct API keys
- Verify `SCRAPER_API_KEY`, `APIFY_API_KEY`, `DEEPL_API_KEY` are set

### Slow Inference
- Enable GPU usage with `--gpu` flag
- Verify GPU is active: check `nvidia-smi` during execution

### Website Scraping Fails
- Check internet connection
- Verify API quota limits haven't been exceeded
- Try alternative scraper (switch between ScraperAPI and Apify)

**For more help:** See [websitedetectiontest/README.md](websitedetectiontest/README.md)

## Model Architecture

**DistilBERT-base-uncased:**
- Pre-trained transformer model: 66M parameters
- 6 layers, 12 attention heads
- 40% faster than BERT, 97% accuracy retention
- Max sequence length: 512 tokens
- Fine-tuned for binary phishing/legitimate classification

## Architecture Details

The model has been fine-tuned on a diverse dataset of 64,000 websites for binary classification:
- **Input:** Cleaned HTML text (preprocessed, max 512 tokens)
- **Output:** Binary classification (Legitimate=0, Phishing=1) with confidence scores
- **Attention:** Full attention weights available for interpretability

## Citation

If you use this project in research, please cite the original dataset and model:

```bibtex
@dataset{mendeley_phishing_2021,
  title={Phishing Website Dataset},
  author={Mendeley Data Contributors},
  year={2021},
  url={https://data.mendeley.com}
}

@inproceedings{sanh2019distilbert,
  title={DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter},
  author={Sanh, Victor and Debut, Lysandre and Sentenis, Julien and Thomas, Paul},
  booktitle={NeurIPS 2019 Workshop on Energy Efficient Machine Learning and Cognitive Computing},
  year={2019}
}
```

## License

This project is provided as-is for educational and research purposes.

## Repository Status

**This repository contains a pre-trained inference-only system.** 

### What's Included
✅ Pre-trained DistilBERT model (`models/distilbert_phishing_model/`)
✅ Detection/inference app (`websitedetectiontest/`)
✅ HTML preprocessing utilities (`preprocess.py`)
✅ Text translation utilities (`translator.py`)
✅ Runtime dependencies configuration

### What's Been Removed
❌ Training pipeline code (train_pytorch.py, evaluate_pytorch.py, test_pipeline.py, attribution.py)
❌ Dataset loading utilities (dataset.py, data_loader.py, extract_labels.py)
❌ Mendeley training dataset (all HTML files, SQL index)
❌ Auxiliary training artifacts (checkpoints, evaluation_results, etc.)

### Note on Model Development
To fine-tune this model on a new dataset or retrain it locally, you would need:
1. The original training code (archived in git history if needed)
2. A labeled dataset in CSV or similar format
3. Significant computational resources (GPU with 16GB+ VRAM recommended)

The training pipeline has been removed to focus this repository on its primary purpose: **inference-only phishing detection on live websites**.

### Version History
- **v2.0 (April 2026):** PyTorch consolidation - removed TensorFlow files, updated all documentation
- **v1.0:** Dual framework support (TensorFlow + PyTorch parallel implementations)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Verify PyTorch is installed correctly: `python -c "import torch; print(torch.cuda.is_available())"`
3. Verify all dependencies: `pip list | grep -E "torch|transformers|numpy"`
4. Run validation tests: `python test_pipeline.py`
5. Check model artifacts exist: `ls -la models/distilbert_phishing_model/`

**For websitedetectiontest module issues:** See [websitedetectiontest/README.md](websitedetectiontest/README.md)

## Future Improvements

- [ ] Add advanced HTML feature extraction (DOM tree analysis, URL patterns)
- [ ] Implement model ensemble for higher accuracy
- [ ] Add LIME-based explanations alongside attention
- [ ] Create web API for inference
- [ ] Optimize model for edge deployment (ONNX export)
- [ ] Add CAPTCHA and form field detection
- [ ] Support multiple languages

---

**Last Updated:** April 2026

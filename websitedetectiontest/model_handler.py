"""
Model inference and prediction with attention-based attribution.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, List, Tuple
import logging
import os

logger = logging.getLogger(__name__)


class PhishingModelHandler:
    """Handles model loading and predictions with explanations."""
    
    def __init__(self, model_path: str):
        """
        Initialize model handler.
        
        Args:
            model_path: Path to model directory (containing config.json, model.safetensors, etc.)
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model path does not exist: {model_path}")
        
        self.model_path = model_path
        self.device = self._get_device()
        
        logger.info(f"Loading model from {model_path}...")
        logger.info(f"Using device: {self.device}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Load model
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        logger.info("Model loaded successfully")
    
    def _get_device(self) -> torch.device:
        """
        Get device (CPU or GPU).
        Defaults to CPU due to RTX 5060 Blackwell incompatibility.
        
        Returns:
            torch.device object
        """
        # Force CPU due to RTX 5060 GPU limitation
        device = torch.device('cpu')
        logger.warning("Forcing CPU inference due to GPU compatibility limitations")
        return device
    
    def _get_important_tokens(self, input_ids: torch.Tensor, attention: torch.Tensor, top_k: int = 10) -> List[Dict]:
        """
        Extract important tokens based on attention weights.
        
        Args:
            input_ids: Tokenized input IDs
            attention: Attention weights from model
            top_k: Number of top tokens to return
            
        Returns:
            List of dicts with token, token_id, importance score
        """
        # Attention shape: (num_layers, batch_size, num_heads, seq_len, seq_len)
        # Get last layer attention for first batch item
        last_layer_attention = attention[-1][0]  # Shape: (num_heads, seq_len, seq_len)
        
        # Average across attention heads to get importance scores
        # Take attention FROM [CLS] token (row 0) across all tokens
        cls_attention = last_layer_attention.mean(dim=0)[0]  # Shape: (seq_len,)
        
        # Get top-k attention scores (excluding [CLS] and [SEP])
        top_k_val = min(top_k, cls_attention.shape[0] - 2)
        top_scores, top_indices = torch.topk(cls_attention[1:-1], top_k_val)
        top_indices = top_indices + 1  # Adjust for excluding [CLS]
        
        important_tokens = []
        
        for i in range(len(top_indices)):
            idx = int(top_indices[i].item())
            score = float(top_scores[i].item())
            token_id = int(input_ids[0, idx].item())
            token_str = self.tokenizer.decode([token_id])
            
            important_tokens.append({
                'token': token_str,
                'token_id': token_id,
                'importance': score,
                'importance_percent': round(score * 100, 2)
            })
        
        return important_tokens
    
    def predict_multiple_sections(self, sections: List[Dict], use_weighted_average: bool = True, 
                                   section_weights: Dict[str, float] = None) -> Dict:
        """
        Predict phishing score for multiple sections and aggregate results with optional weighting.
        
        Conversion sections (bottom) are weighted higher as they contain scam signals.
        
        Args:
            sections: List of section dicts from processor (with 'name' and 'text')
            use_weighted_average: Whether to use weighted averaging instead of simple average
            section_weights: Custom weights for sections (default: top=0.2, middle=0.3, bottom=0.5)
            
        Returns:
            Dictionary with:
                - section_predictions: List of predictions per section
                - aggregate_phishing_probability: Weighted phishing probability
                - aggregate_legitimate_probability: Weighted legitimate probability
                - aggregate_confidence: Aggregate confidence
                - aggregate_predicted_label: Overall prediction
                - aggregation_method: 'weighted' or 'simple_average'
                - weights_used: Weights applied to sections
        """
        # Default weights: bottom section (conversion/earnings) gets highest weight
        if section_weights is None:
            section_weights = {
                'top': 0.2,
                'middle': 0.3,
                'bottom': 0.5,
            }
        
        logger.info(f"Running predictions for {len(sections)} sections...")
        if use_weighted_average:
            logger.info(f"Using weighted aggregation: {section_weights}")
        
        section_predictions = []
        all_phishing_probs = []
        all_legitimate_probs = []
        weights_applied = []
        
        for section in sections:
            section_name = section.get('name', 'unknown').lower()
            section_text = section.get('text', '')
            
            if not section_text or len(section_text) < 10:
                continue
                
            pred = self.predict(section_text, include_explanation=False)
            all_phishing_probs.append(pred['phishing_probability'])
            all_legitimate_probs.append(pred['legitimate_probability'])
            
            # Get weight for this section
            weight = section_weights.get(section_name, 1.0 / len(sections))
            weights_applied.append(weight)
            
            section_predictions.append({
                'section_name': section_name,
                'predicted_class': pred['predicted_class'],
                'predicted_label': pred['predicted_label'],
                'phishing_probability': pred['phishing_probability'],
                'legitimate_probability': pred['legitimate_probability'],
                'confidence': pred['confidence'],
                'weight': weight,  # Include weight in result
            })
        
        # Aggregate predictions
        if use_weighted_average and weights_applied:
            # Weighted average
            total_weight = sum(weights_applied)
            weights_normalized = [w / total_weight for w in weights_applied]
            
            avg_phishing = sum(p * w for p, w in zip(all_phishing_probs, weights_normalized))
            avg_legitimate = sum(p * w for p, w in zip(all_legitimate_probs, weights_normalized))
            aggregation_method = 'weighted_average'
        else:
            # Simple average
            avg_phishing = sum(all_phishing_probs) / len(all_phishing_probs) if all_phishing_probs else 0.5
            avg_legitimate = sum(all_legitimate_probs) / len(all_legitimate_probs) if all_legitimate_probs else 0.5
            aggregation_method = 'simple_average'
        
        avg_confidence = max(avg_phishing, avg_legitimate)
        aggregate_class = int(avg_phishing > avg_legitimate)
        aggregate_label = 'Phishing' if aggregate_class == 1 else 'Legitimate'
        
        result = {
            'section_predictions': section_predictions,
            'aggregate_phishing_probability': round(avg_phishing, 4),
            'aggregate_legitimate_probability': round(avg_legitimate, 4),
            'aggregate_confidence': round(avg_confidence, 4),
            'aggregate_predicted_label': aggregate_label,
            'section_count': len(section_predictions),
            'aggregation_method': aggregation_method,
            'weights_used': section_weights,
        }
        
        logger.info(f"Multi-section prediction ({aggregation_method}): {aggregate_label} ({avg_confidence:.2%} confidence)")
        
        return result
    
    def predict(self, cleaned_text: str, include_explanation: bool = True) -> Dict:
        """
        Predict phishing score for cleaned text.
        
        Args:
            cleaned_text: Preprocessed text from processor
            include_explanation: Whether to include token importance scores
            
        Returns:
            Dictionary with:
                - predicted_class: 0 (Legitimate) or 1 (Phishing)
                - predicted_label: 'Legitimate' or 'Phishing'
                - legitimate_probability: float [0, 1]
                - phishing_probability: float [0, 1]
                - confidence: float [0, 1] (max probability)
                - top_important_tokens: List[Dict] (if include_explanation=True)
        """
        logger.info("Running model prediction...")
        
        # Tokenize
        inputs = self.tokenizer(
            cleaned_text,
            max_length=512,
            padding='max_length',
            truncation=True,
            add_special_tokens=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        # Move to device
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        # Get model predictions
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_attentions=include_explanation
            )
        
        # Extract logits
        logits = outputs.logits[0].cpu()
        probabilities = torch.softmax(logits, dim=0).numpy()
        
        legitimate_prob = float(probabilities[0])
        phishing_prob = float(probabilities[1])
        
        predicted_class = int(phishing_prob > legitimate_prob)
        predicted_label = 'Phishing' if predicted_class == 1 else 'Legitimate'
        confidence = max(legitimate_prob, phishing_prob)
        
        # Extract token information
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0].cpu().numpy())
        non_padding_count = len([t for t in tokens if t != '[PAD]'])
        
        # Check text length for reliability assessment
        text_length = len(cleaned_text)
        if text_length < 300:
            reliability = 'LOW - Short text may have unreliable predictions'
            confidence_flag = True
        elif text_length < 512:
            reliability = 'MEDIUM - Limited text for robust analysis'
            confidence_flag = True
        else:
            reliability = 'HIGH - Sufficient text for reliable prediction'
            confidence_flag = False
        
        result = {
            'predicted_class': predicted_class,
            'predicted_label': predicted_label,
            'legitimate_probability': round(legitimate_prob, 4),
            'phishing_probability': round(phishing_prob, 4),
            'confidence': round(confidence, 4),
            'tokens': tokens,
            'token_count': non_padding_count,
            'text_length': text_length,
            'reliability': reliability,
            'low_confidence_flag': confidence_flag
        }
        
        # Get important tokens if requested
        if include_explanation and outputs.attentions is not None:
            important_tokens = self._get_important_tokens(
                input_ids,
                outputs.attentions,
                top_k=15
            )
            result['top_important_tokens'] = important_tokens
        
        logger.info(f"Prediction: {predicted_label} (confidence: {confidence:.2%})")
        
        return result

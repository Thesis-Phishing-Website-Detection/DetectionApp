"""
HTML dashboard generation for phishing detection results.
"""
from jinja2 import Template, Environment, select_autoescape
from typing import Dict, List
import logging
import hashlib
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# HTML Template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phishing Detection Result - {{ url }}</title>
    <script>
        // Define function early so onclick handlers can reference it
        function toggleCollapsible(element) {
            const content = element.nextElementSibling;
            content.classList.toggle('active');
            const arrow = element.querySelector('span:last-child');
            arrow.textContent = content.classList.contains('active') ? '▲' : '▼';
        }
    </script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .timestamp {
            font-size: 0.9em;
            opacity: 0.7;
            margin-top: 10px;
        }
        
        .content {
            padding: 40px;
        }
        
        .result-card {
            background: {{ result_bg_color }};
            border-left: 5px solid {{ result_border_color }};
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .result-label {
            font-size: 2.5em;
            font-weight: bold;
            color: {{ result_text_color }};
            margin-bottom: 10px;
        }
        
        .result-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .detail-item {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .detail-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
        }
        
        .detail-value {
            font-size: 1.8em;
            font-weight: bold;
            color: {{ result_text_color }};
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .url-box {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            word-break: break-all;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            color: #333;
        }
        
        .preprocessing-steps {
            list-style: none;
            padding: 0;
        }
        
        .preprocessing-steps li {
            background: #f9f9f9;
            padding: 12px 15px;
            margin-bottom: 8px;
            border-radius: 4px;
            border-left: 4px solid #667eea;
            font-size: 0.95em;
        }
        
        .preprocessing-steps li:before {
            content: "✓ ";
            color: #28a745;
            font-weight: bold;
            margin-right: 8px;
        }
        
        .text-preview {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            line-height: 1.8;
            max-height: 400px;
            overflow-y: auto;
            word-wrap: break-word;
            white-space: pre-wrap;
            border: 2px solid #e0e0e0;
            margin-bottom: 20px;
            display: block;
            visibility: visible;
        }
        
        .token-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .token-stat {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e0e0e0;
        }
        
        .token-stat-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
        }
        
        .token-stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        
        .tokens-list {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            max-height: 250px;
            overflow-y: auto;
            border: 1px solid #ddd;
        }
        
        .token-item {
            display: inline-block;
            background: #e8eaf6;
            color: #667eea;
            padding: 5px 10px;
            margin: 5px 5px 5px 0;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        
        .important-tokens {
            list-style: none;
            padding: 0;
        }
        
        .important-tokens li {
            background: #f9f9f9;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 4px solid {{ result_border_color }};
        }
        
        .token-bar {
            display: flex;
            align-items: center;
            margin-top: 10px;
            gap: 15px;
        }
        
        .token-text {
            font-family: 'Courier New', monospace;
            font-weight: bold;
            min-width: 120px;
            color: #333;
        }
        
        .bar-container {
            flex: 1;
            height: 25px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, {{ result_border_color }});
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .raw-html-preview {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            overflow-x: auto;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #444;
        }
        
        .footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }
        
        .truncation-warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
        }
        
        .collapsible {
            cursor: pointer;
            user-select: none;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 4px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .collapsible:hover {
            background: #e8e8e8;
        }
        
        .collapsible-content {
            display: none;
            margin-top: 10px;
        }
        
        .collapsible-content.active {
            display: block;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .result-details {
                grid-template-columns: 1fr;
            }
            
            .content {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Phishing Detection Analysis</h1>
            <p id="urlDisplay">{{ url }}</p>
            <div class="timestamp">{{ timestamp }}</div>
        </div>
        
        <div class="content">
            <!-- Section Predictions (if multi-section analysis) -->
            {% if prediction_result.section_predictions %}
            <div class="section">
                <div class="section-title">📊 Multi-Section Analysis Results</div>
                <p style="color: #666; margin-bottom: 15px; font-size: 0.95em;">
                    The page was analyzed in {{ prediction_result.section_count }} sections for better accuracy:
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    {% for section_pred in prediction_result.section_predictions %}
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 4px solid {% if section_pred.predicted_label == 'Phishing' %}#d32f2f{% else %}#2e7d32{% endif %};">
                        <div style="font-weight: bold; margin-bottom: 10px; color: #333;">{{ section_pred.section_name }}</div>
                        <div style="font-size: 1.5em; font-weight: bold; color: {% if section_pred.predicted_label == 'Phishing' %}#b71c1c{% else %}#1b5e20{% endif %}; margin-bottom: 8px;">
                            {{ section_pred.predicted_label }}
                        </div>
                        <div style="font-size: 0.85em; color: #666;">
                            <div>Phishing: <strong>{{ section_pred.phishing_probability | round(2) }}%</strong></div>
                            <div>Legitimate: <strong>{{ section_pred.legitimate_probability | round(2) }}%</strong></div>
                            <div>Confidence: <strong>{{ section_pred.confidence | round(2) }}%</strong></div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                <p style="background: #e8f5e9; padding: 12px; border-radius: 6px; color: #1b5e20; border-left: 4px solid #2e7d32; font-size: 0.9em;">
                    <strong>Aggregate Result:</strong> The final prediction is based on averaging probabilities across all sections for more robust detection.
                </p>
            </div>
            {% endif %}
            
            
            <!-- Section Analysis with Scam Patterns -->
            {% if weighted_predictions and pattern_detection %}
            <div class="section">
                <div class="section-title">📍 Section Analysis & Scam Patterns</div>
                <p style="color: #666; margin-bottom: 15px; font-size: 0.95em;">
                    Each page section analyzed for phishing classification and scam indicators. Bottom section carries highest risk due to conversion content.
                </p>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    {% for section in weighted_predictions.section_predictions %}
                    <div style="background: white; border: 2px solid {% if section.predicted_label == 'Phishing' %}#d32f2f{% else %}#2e7d32{% endif %}; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <!-- Section Header -->
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <div style="font-size: 1.3em; font-weight: bold; color: #333;">{{ section.section_name | upper }}</div>
                                <div style="background: {% if section.predicted_label == 'Phishing' %}#ffebee{% else %}#e8f5e9{% endif %}; padding: 8px 12px; border-radius: 20px; font-weight: bold; color: {% if section.predicted_label == 'Phishing' %}#b71c1c{% else %}#1b5e20{% endif %}; font-size: 0.9em;">
                                    {{ section.predicted_label }}
                                </div>
                            </div>
                            <div style="font-size: 0.85em; color: #666;">
                                <div>Phishing: <strong>{{ section.phishing_probability }}%</strong> | Legitimate: <strong>{{ section.legitimate_probability }}%</strong></div>
                                <div>Confidence: <strong>{{ section.confidence }}%</strong> | Weight: <strong>{{ section.weight | round(0) }}%</strong></div>
                            </div>
                        </div>
                        
                        <!-- Scam Pattern Indicators for this Section -->
                        <div style="background: #f5f5f5; padding: 12px; border-radius: 6px; border-left: 3px solid #667eea;">
                            <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px; color: #333;">Scam Indicators:</div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.9em;">
                                <div>💰 Earning Claims: <span style="font-weight: bold; color: {% if pattern_detection.earning_claims|length > 0 %}#ff6f00{% else %}#28a745{% endif %};">{{ pattern_detection.earning_claims|length }}</span></div>
                                <div>👥 Testimonials: <span style="font-weight: bold; color: {% if pattern_detection.testimonials|length > 0 %}#e91e63{% else %}#28a745{% endif %};">{{ pattern_detection.testimonials|length }}</span></div>
                                <div>⏰ Urgency: <span style="font-weight: bold; color: {% if pattern_detection.urgency_tactics|length > 0 %}#f57c00{% else %}#28a745{% endif %};">{{ pattern_detection.urgency_tactics|length }}</span></div>
                                <div>✓ False Legitimacy: <span style="font-weight: bold; color: {% if pattern_detection.fake_legitimacy|length > 0 %}#9c27b0{% else %}#28a745{% endif %};">{{ pattern_detection.fake_legitimacy|length }}</span></div>
                            </div>
                            {% if pattern_detection.testimonial_clustering.is_clustered %}
                            <div style="margin-top: 10px; padding: 8px; background: #ffe0f2; border-radius: 4px; font-size: 0.9em; color: #c2185b; font-weight: bold;">
                                🚨 Testimonial Clustering: {{ pattern_detection.testimonial_clustering.testimonial_count }} testimonials detected
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Overall Pattern Risk -->
                <div style="background: {% if pattern_detection.risk_level == 'CRITICAL' %}#ffebee{% elif pattern_detection.risk_level == 'HIGH' %}#fff3e0{% else %}#e8f5e9{% endif %}; 
                            border-left: 4px solid {% if pattern_detection.risk_level == 'CRITICAL' %}#d32f2f{% elif pattern_detection.risk_level == 'HIGH' %}#f57c00{% else %}#2e7d32{% endif %}; 
                            padding: 20px; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 1.1em; font-weight: bold; color: {% if pattern_detection.risk_level == 'CRITICAL' %}#b71c1c{% elif pattern_detection.risk_level == 'HIGH' %}#e65100{% else %}#1b5e20{% endif %}; margin-bottom: 5px;">
                                Overall Scam Risk: {{ pattern_detection.risk_level }}
                            </div>
                            <div style="font-size: 0.9em; color: #666;">
                                Total: {{ pattern_detection.earning_claims|length + pattern_detection.testimonials|length + pattern_detection.urgency_tactics|length + pattern_detection.fake_legitimacy|length }} suspicious indicators detected
                            </div>
                        </div>
                        <div style="font-size: 2.5em; font-weight: bold; color: {% if pattern_detection.risk_level == 'CRITICAL' %}#b71c1c{% elif pattern_detection.risk_level == 'HIGH' %}#e65100{% else %}#1b5e20{% endif %};">
                            {{ pattern_detection.risk_score | round(1) }}%
                        </div>
                    </div>
                    {% if pattern_detection.flagged %}
                    <div style="margin-top: 15px; padding: 12px; background: rgba(0,0,0,0.1); border-radius: 4px; font-weight: bold; color: {% if pattern_detection.risk_level == 'CRITICAL' %}#b71c1c{% else %}#e65100{% endif %}; text-align: center;">
                        🚨 FLAGGED - Potential scam detected
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endif %}
            
            <!-- Final Assessment -->
            {% if final_assessment %}
            <div class="section">
                <div class="section-title">📋 Combined Assessment</div>
                <div style="background: {% if final_assessment.combined_recommendation == 'Phishing' or 'Likely Phishing' in final_assessment.combined_recommendation %}#ffebee{% else %}#e8f5e9{% endif %}; 
                            border-left: 4px solid {% if final_assessment.combined_recommendation == 'Phishing' or 'Likely Phishing' in final_assessment.combined_recommendation %}#d32f2f{% else %}#2e7d32{% endif %}; 
                            padding: 20px; border-radius: 8px;">
                    <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 15px; color: {% if final_assessment.combined_recommendation == 'Phishing' or 'Likely Phishing' in final_assessment.combined_recommendation %}#b71c1c{% else %}#1b5e20{% endif %};">
                        {{ final_assessment.combined_recommendation }}
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div style="background: rgba(255,255,255,0.5); padding: 12px; border-radius: 6px;">
                            <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">ML Model</div>
                            <div style="font-size: 1.3em; font-weight: bold; color: {% if final_assessment.ml_prediction == 'Phishing' %}#d32f2f{% else %}#2e7d32{% endif %};">
                                {{ final_assessment.ml_prediction }}
                            </div>
                            <div style="font-size: 0.9em; color: #666; margin-top: 5px;">Confidence: {{ final_assessment.ml_confidence | round(1) }}%</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.5); padding: 12px; border-radius: 6px;">
                            <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Pattern Detection</div>
                            <div style="font-size: 1.3em; font-weight: bold; color: {% if final_assessment.pattern_risk == 'CRITICAL' or final_assessment.pattern_risk == 'HIGH' %}#f57c00{% else %}#667eea{% endif %};">
                                {{ final_assessment.pattern_risk }}
                            </div>
                            <div style="font-size: 0.9em; color: #666; margin-top: 5px;">Risk: {{ final_assessment.pattern_risk_score | round(1) }}%</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.5); padding: 12px; border-radius: 6px;">
                            <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Combined Confidence</div>
                            <div style="font-size: 1.3em; font-weight: bold; color: #667eea;">
                                {{ final_assessment.boosted_confidence | round(1) }}%
                            </div>
                            <div style="font-size: 0.9em; color: #999; margin-top: 5px;">Boosted from ML</div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
            {% if crypto_gambling_detection %}
            <div style="margin: 30px 0;">
                {% if crypto_gambling_detection.crypto_phishing.detected or crypto_gambling_detection.gambling.detected %}
                    {% if crypto_gambling_detection.crypto_phishing.detected %}
                    <div style="background: #ffebee; border-left: 4px solid #d32f2f; padding: 20px; border-radius: 6px; margin-bottom: 15px;">
                        <div style="color: #c62828; font-weight: bold; font-size: 1.1em; margin-bottom: 10px;">🚨 CRYPTO PHISHING DETECTED</div>
                        <div style="color: #b71c1c; line-height: 1.6;">
                            <strong>Confidence:</strong> {{ crypto_gambling_detection.crypto_phishing.details.confidence | round(1) }}%<br>
                            <strong>Evidence:</strong> {{ crypto_gambling_detection.crypto_phishing.details.evidence_count }} indicators found<br>
                            {% if crypto_gambling_detection.crypto_phishing.details.detected_keywords %}
                            <strong>Crypto Keywords:</strong> {{ crypto_gambling_detection.crypto_phishing.details.detected_keywords | length }} detected
                            <div style="margin-top: 10px; background: #fff; padding: 10px; border-radius: 4px;">
                                {% for keyword, count in crypto_gambling_detection.crypto_phishing.details.detected_keywords %}
                                {% if loop.index0 < 5 %}
                                <span style="background: #ffcdd2; color: #c62828; padding: 4px 8px; margin: 4px 4px 4px 0; border-radius: 3px; display: inline-block; font-size: 0.9em;">{{ keyword }} ({{ count }}x)</span>
                                {% endif %}
                                {% endfor %}
                            </div>
                            {% endif %}
                            {% if crypto_gambling_detection.crypto_phishing.details.risk_factors %}
                            <strong style="display: block; margin-top: 10px;">Risk Factors:</strong>
                            <ul style="margin-left: 20px; margin-top: 5px;">
                                {% for factor in crypto_gambling_detection.crypto_phishing.details.risk_factors %}
                                {% if loop.index0 < 5 %}
                                <li style="color: #b71c1c;">{{ factor }}</li>
                                {% endif %}
                                {% endfor %}
                            </ul>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if crypto_gambling_detection.gambling.detected %}
                    <div style="background: #fff3e0; border-left: 4px solid #f57c00; padding: 20px; border-radius: 6px; margin-bottom: 15px;">
                        <div style="color: #e65100; font-weight: bold; font-size: 1.1em; margin-bottom: 10px;">🎰 GAMBLING/BETTING WEBSITE DETECTED</div>
                        <div style="color: #d84315; line-height: 1.6;">
                            <strong>Confidence:</strong> {{ crypto_gambling_detection.gambling.details.confidence | round(1) }}%<br>
                            <strong>Type:</strong> {{ crypto_gambling_detection.gambling.details.gambling_type | join(', ') }}<br>
                            <strong>Evidence:</strong> {{ crypto_gambling_detection.gambling.details.evidence_count }} indicators found<br>
                            {% if crypto_gambling_detection.gambling.details.detected_keywords %}
                            <strong>Gambling Keywords:</strong> {{ crypto_gambling_detection.gambling.details.detected_keywords | length }} detected
                            <div style="margin-top: 10px; background: #fff; padding: 10px; border-radius: 4px;">
                                {% for keyword, count in crypto_gambling_detection.gambling.details.detected_keywords %}
                                {% if loop.index0 < 5 %}
                                <span style="background: #ffe0b2; color: #e65100; padding: 4px 8px; margin: 4px 4px 4px 0; border-radius: 3px; display: inline-block; font-size: 0.9em;">{{ keyword }} ({{ count }}x)</span>
                                {% endif %}
                                {% endfor %}
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                {% else %}
                <div style="background: #e8f5e9; border-left: 4px solid #2e7d32; padding: 15px; border-radius: 6px; color: #1b5e20;">
                    <strong>✓ No crypto phishing or gambling indicators detected</strong>
                </div>
                {% endif %}
            </div>
            {% endif %}
            
            <!-- Reliability Warning -->
            {% if reliability_warning %}
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <div style="color: #856404; font-weight: bold; margin-bottom: 8px;">⚠️ Prediction Reliability Notice</div>
                <div style="color: #856404; font-size: 0.95em; line-height: 1.5;">
                    {{ reliability_warning }}<br>
                    <strong>Text analyzed:</strong> {{ text_length }} characters ({{ token_count }} tokens)<br>
                    <strong>Recommendation:</strong> For more reliable results, ensure websites have substantial visible content (&gt;500 characters).
                </div>
            </div>
            {% endif %}
            
            <!-- Input Section -->
            <div class="section">
                <div class="section-title">📝 Input URL</div>
                <div class="url-box">{{ url }}</div>
            </div>
            
            <!-- Raw HTML Preview -->
            <div class="section">
                <div class="section-title">🌐 Raw HTML (First 500 chars)</div>
                <div class="collapsible" onclick="toggleCollapsible(this)">
                    <span>Click to expand raw HTML preview</span>
                    <span>▼</span>
                </div>
                <div class="collapsible-content">
                    <div class="raw-html-preview">{{ raw_html_preview }}</div>
                </div>
            </div>
            
            <!-- Preprocessing Steps -->
            <div class="section">
                <div class="section-title">⚙️ Preprocessing Steps</div>
                <ul class="preprocessing-steps">
                    {% for step in preprocessing_steps %}
                    <li>{{ step }}</li>
                    {% endfor %}
                </ul>
            </div>
            
            <!-- Cleaned Text -->
            <div class="section">
                <div class="section-title">✂️ Cleaned Text (Ready for Model)</div>
                {% if was_truncated %}
                <div class="truncation-warning">
                    ⚠️ Text was truncated to 512 characters ({{ original_char_count }} → {{ cleaned_char_count }} chars)
                </div>
                {% else %}
                <p style="color: #666; margin-bottom: 15px; font-size: 0.95em;">
                    Text length: {{ cleaned_char_count }} characters (no truncation needed)
                </p>
                {% endif %}
                <div class="text-preview">{{ cleaned_text }}</div>
            </div>
            
            <!-- Tokenization Info -->
            <div class="section">
                <div class="section-title">🔤 Tokenization Details</div>
                <div class="token-info">
                    <div class="token-stat">
                        <div class="token-stat-label">Non-Padding Tokens</div>
                        <div class="token-stat-value">{{ token_count }}</div>
                    </div>
                    <div class="token-stat">
                        <div class="token-stat-label">Total Tokens (with padding)</div>
                        <div class="token-stat-value">512</div>
                    </div>
                </div>
                
                <p style="margin-top: 20px; color: #666; font-size: 0.95em;">
                    <strong>First 50 tokens:</strong>
                </p>
                <div class="tokens-list">
                    {% for token in tokens_preview %}
                    <span class="token-item">{{ token }}</span>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Important Tokens (Attribution) -->
            {% if important_tokens %}
            <div class="section">
                <div class="section-title">⭐ Most Important Tokens (Attention-Based Attribution)</div>
                <p style="color: #666; margin-bottom: 20px; font-size: 0.95em;">
                    These tokens had the highest attention weights and most influenced the prediction:
                </p>
                <ul class="important-tokens">
                    {% for token_info in important_tokens %}
                    <li>
                        <div class="token-bar">
                            <div class="token-text">{{ token_info.token }}</div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: {{ token_info.importance_percent }}%;">
                                    {{ token_info.importance_percent }}%
                                </div>
                            </div>
                        </div>
                    </li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            Generated on {{ timestamp }} | Powered by DistilBERT Phishing Detection Model
        </div>
    </div>
    
    <script>
        // URL truncation for display if too long
        const urlDisplay = document.getElementById('urlDisplay');
        if (urlDisplay && urlDisplay.textContent.length > 80) {
            urlDisplay.textContent = urlDisplay.textContent.substring(0, 77) + '...';
        }
    </script>
</body>
</html>
"""


class DashboardGenerator:
    """Generate interactive HTML dashboard for phishing detection results."""
    
    @staticmethod
    def _generate_filename(url: str) -> str:
        """Generate safe filename from URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{url_hash}_dashboard.html"
    
    @staticmethod
    def generate_dashboard(
        url: str,
        raw_html: str,
        processor_result: Dict,
        prediction_result: Dict,
        output_dir: str
    ) -> str:
        """
        Generate and save HTML dashboard.
        
        Args:
            url: Website URL
            raw_html: Raw HTML content
            processor_result: Output from ContentProcessor.process_html()
            prediction_result: Output from PhishingModelHandler.predict()
            output_dir: Directory to save dashboard HTML
            
        Returns:
            Path to generated HTML file
        """
        logger.info("Generating dashboard HTML...")
        
        # Prepare variables for template
        cleaned_text = processor_result['cleaned_text']
        formatted_text = cleaned_text  # Display cleaned text as-is
        preprocessing_steps = processor_result.get('preprocessing_steps', ['HTML cleaning', 'Text extraction', 'Normalization'])
        
        phishing_prob = prediction_result['phishing_probability']
        legitimate_prob = prediction_result['legitimate_probability']
        confidence = prediction_result['confidence']
        predicted_label = prediction_result['predicted_label']
        
        # Determine color scheme based on prediction
        if predicted_label == 'Phishing':
            result_bg_color = '#ffe8e8'
            result_border_color = '#d32f2f'
            result_text_color = '#b71c1c'
        else:
            result_bg_color = '#e8f5e9'
            result_border_color = '#2e7d32'
            result_text_color = '#1b5e20'
        
        # Prepare tokens preview (first 50)
        tokens = prediction_result.get('tokens', [])
        tokens_preview = [t for t in tokens if t != '[PAD'][:50]
        
        # Prepare raw HTML preview
        raw_html_preview = raw_html[:500].replace('<', '&lt;').replace('>', '&gt;')
        
        # Prepare important tokens
        important_tokens = prediction_result.get('top_important_tokens', [])
        
        # Normalize probabilities to percentage
        phishing_percentage = round(phishing_prob * 100, 2)
        legitimate_percentage = round(legitimate_prob * 100, 2)
        confidence_percentage = round(confidence * 100, 2)
        
        # Normalize section predictions percentages
        normalized_sections = []
        section_preds = prediction_result.get('section_predictions', {})
        
        # Handle both dict format (from main.py) and list format (legacy)
        if isinstance(section_preds, dict):
            for section_name, sec_pred in section_preds.items():
                normalized_sections.append({
                    'section_name': section_name.capitalize(),
                    'predicted_label': sec_pred['predicted_label'],
                    'phishing_probability': round(sec_pred['phishing_probability'] * 100, 2),
                    'legitimate_probability': round(sec_pred['legitimate_probability'] * 100, 2),
                    'confidence': round(sec_pred['confidence'] * 100, 2)
                })
        else:
            # Legacy list format
            for sec_pred in section_preds:
                normalized_sections.append({
                    'section_name': sec_pred['section_name'],
                    'predicted_label': sec_pred['predicted_label'],
                    'phishing_probability': round(sec_pred['phishing_probability'] * 100, 2),
                    'legitimate_probability': round(sec_pred['legitimate_probability'] * 100, 2),
                    'confidence': round(sec_pred['confidence'] * 100, 2)
                })
        
        # Prepare template context
        context = {
            'url': url,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'prediction_label': predicted_label,
            'phishing_probability': phishing_percentage,
            'legitimate_probability': legitimate_percentage,
            'confidence': confidence_percentage,
            'result_bg_color': result_bg_color,
            'result_border_color': result_border_color,
            'result_text_color': result_text_color,
            'raw_html_preview': raw_html_preview,
            'preprocessing_steps': preprocessing_steps,
            'cleaned_text': formatted_text,  # Use formatted version for display
            'cleaned_char_count': len(cleaned_text),
            'original_char_count': len(raw_html),
            'was_truncated': processor_result['was_truncated'],
            'tokens_preview': tokens_preview,
            'token_count': prediction_result.get('token_count', 0),
            'text_length': prediction_result.get('text_length', len(cleaned_text)),
            'reliability_warning': prediction_result.get('reliability', None),
            'important_tokens': important_tokens,
            'crypto_gambling_detection': prediction_result.get('crypto_gambling_detection', None),
            'pattern_detection': prediction_result.get('pattern_detection', None),
            'weighted_predictions': prediction_result.get('weighted_predictions', None),
            'final_assessment': prediction_result.get('final_assessment', None),
            'prediction_result': {
                'section_predictions': normalized_sections,
                'section_count': len(normalized_sections)
            }
        }
        
        # Render template with autoescaping to prevent HTML/JS injection
        env = Environment(autoescape=select_autoescape(['html', 'xml']))
        template = env.from_string(DASHBOARD_TEMPLATE)
        html_content = template.render(**context)
        
        # Save to file
        os.makedirs(output_dir, exist_ok=True)
        filename = DashboardGenerator._generate_filename(url)
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Dashboard saved to {output_path}")
        
        return output_path

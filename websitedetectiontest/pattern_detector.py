"""
Pattern detection for common phishing and scam indicators.
Detects extreme earning claims, fake testimonials, urgency tactics, and more.
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects phishing patterns in text that bypass ML models."""
    
    # Extreme earning/money claim patterns
    EARNING_CLAIM_PATTERNS = [
        r'\b(?:earn|make|get|profit|gain|money|cash|income|revenue|withdraw|payment|payout)\s+(?:up\s+)?to\s+\$?\d+[,.]?\d*(?:\s*(?:per|a|per\s+day|daily|weekly|monthly|hour))?',
        r'\b(?:\$?\d+[,.]?\d*)\s+(?:per\s+day|daily|per\s+hour|hourly|per\s+week|weekly)',
        r'(?:easy\s+)?(?:quick\s+)?money(?:\s+(?:fast|easy|quick|guaranteed))?',
        r'guaranteed\s+(?:income|earnings|profit|return|payment)',
        r'(?:no\s+)?experience\s+(?:needed|required|necessary)',
        r'work\s+from\s+(?:home|bed|anywhere)',
        r'(?:passive|extra)\s+income',
    ]
    
    # Fake testimonial patterns
    TESTIMONIAL_PATTERNS = [
        r'(?:i\s+)?(?:made|earned|got|received)\s+\$?\d+[,.]?\d*',  # "I made $500"
        r'(?:i\s+)?(?:was\s+)?(?:unemployed|struggling|broke|broke)',  # Context
        r'(?:member\s+(?:for|since|in))(?:\s+(?:\d+\s+)?(?:day|week|month)s?)?(?:\s+ago)?',
        r'(?:easy|simple|amazing|incredible|best)\s+(?:experience|opportunity|platform)',
        r'(?:can\'?t\s+)?believe\s+(?:it|this|how\s+(?:easy|much))',
        r'(?:support|team)\s+(?:is\s+)?(?:amazing|incredible|best|helpful)',
        r'(?:started\s+)?(?:slowly|from\s+zero)',
    ]
    
    # Urgency/Pressure patterns
    URGENCY_PATTERNS = [
        r'(?:limited|limited\s+time|urgent|hurry|act\s+now|don\'?t\s+(?:wait|miss))',
        r'(?:only|just)\s+\d+\s+(?:spots|places|members|slots)\s+(?:left|available|remaining)',
        r'(?:join\s+)?now\s+(?:before\s+)?(?:it\'?s|they\'?re)\s+gone',
        r'(?:last\s+chance|final\s+offer|last\s+day)',
    ]
    
    # Authority/Legitimacy mimicking patterns
    FAKE_LEGITIMACY_PATTERNS = [
        r'(?:official|verified|licensed|certified|registered)\s+(?:partner|affiliate|member)',
        r'(?:over|more\s+than)\s+\d+[,+]\d+\s+(?:members|people|brazilians|users)',
        r'(?:\d+%\s+)?(?:satisfaction|success|approval|happy)',
        r'(?:trusted\s+by|used\s+by|partners?\s+with)\s+\w+',
    ]
    
    # Testimonial clustering (multiple testimonials in sequence)
    TESTIMONIAL_BLOCK_PATTERN = r'(?:["\']?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*["\']?\s+(?:Member|User|Person|Customer).*?(?:[\.\!\?]|$))(?=\s*(?:["\']?[A-Z][a-z]+|$))'
    
    @classmethod
    def detect_patterns(cls, text: str) -> Dict:
        """
        Detect phishing/scam patterns in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detection results and risk score
        """
        text_lower = text.lower()
        results = {
            'earning_claims': cls._detect_pattern_group(text_lower, cls.EARNING_CLAIM_PATTERNS),
            'testimonials': cls._detect_pattern_group(text_lower, cls.TESTIMONIAL_PATTERNS),
            'urgency_tactics': cls._detect_pattern_group(text_lower, cls.URGENCY_PATTERNS),
            'fake_legitimacy': cls._detect_pattern_group(text_lower, cls.FAKE_LEGITIMACY_PATTERNS),
            'testimonial_clustering': cls._detect_testimonial_clustering(text),
            'risk_score': 0.0,
            'risk_level': 'LOW',
            'flagged': False,
        }
        
        # Calculate risk score
        results['risk_score'] = cls._calculate_risk_score(results)
        
        # Determine risk level and flag if needed
        if results['risk_score'] >= 0.7:
            results['risk_level'] = 'CRITICAL'
            results['flagged'] = True
        elif results['risk_score'] >= 0.5:
            results['risk_level'] = 'HIGH'
            results['flagged'] = True
        elif results['risk_score'] >= 0.3:
            results['risk_level'] = 'MEDIUM'
        
        logger.info(f"Pattern detection: Risk={results['risk_level']} ({results['risk_score']:.2%})")
        if results['flagged']:
            logger.warning(f"  FLAGGED - Detected scam patterns: "
                          f"Earning claims ({len(results['earning_claims'])}), "
                          f"Testimonials ({len(results['testimonials'])})")
        
        return results
    
    @classmethod
    def _detect_pattern_group(cls, text: str, patterns: List[str]) -> List[Dict]:
        """
        Detect multiple patterns in text.
        
        Args:
            text: Text to search
            patterns: List of regex patterns
            
        Returns:
            List of detected pattern matches
        """
        detections = []
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    detections.append({
                        'pattern': pattern[:50],  # Truncate for logging
                        'match': match.group(0),
                        'position': match.start(),
                    })
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {e}")
        
        return detections
    
    @classmethod
    def _detect_testimonial_clustering(cls, text: str) -> Dict:
        """
        Detect multiple testimonials clustered together (common in scams).
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with clustering information
        """
        # Look for patterns like: "Name Person..." repeated multiple times
        name_patterns = re.findall(
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Member|Person|User|Customer)',
            text
        )
        
        testimonial_count = len(name_patterns)
        
        # Look for fake testimonial phrases
        fake_phrases = [
            'member for', 'member since', 'days ago', 'month ago', 
            'i made', 'i earned', 'i got', 'i started',
            'incredible', 'amazing', 'can\'t believe'
        ]
        
        phrase_count = sum(
            len(re.findall(re.escape(phrase), text, re.IGNORECASE))
            for phrase in fake_phrases
        )
        
        return {
            'testimonial_count': testimonial_count,
            'fake_phrase_count': phrase_count,
            'clustering_score': min(1.0, (testimonial_count + phrase_count / 2) / 10),
            'is_clustered': testimonial_count >= 3 and phrase_count >= 5,
        }
    
    @classmethod
    def _calculate_risk_score(cls, results: Dict) -> float:
        """
        Calculate overall risk score from detected patterns.
        
        Args:
            results: Dictionary with all detection results
            
        Returns:
            Risk score between 0.0 and 1.0
        """
        score = 0.0
        
        # Earning claims are high-risk indicators
        if results['earning_claims']:
            score += min(0.3, len(results['earning_claims']) * 0.1)
        
        # Testimonials + clustering is a strong scam signal
        if results['testimonials'] and results['testimonial_clustering']['is_clustered']:
            score += 0.35
        elif results['testimonials']:
            score += min(0.2, len(results['testimonials']) * 0.05)
        
        # Testimonial clustering alone
        if results['testimonial_clustering']['is_clustered']:
            score += results['testimonial_clustering']['clustering_score'] * 0.15
        
        # Urgency tactics
        if results['urgency_tactics']:
            score += min(0.15, len(results['urgency_tactics']) * 0.05)
        
        # Fake legitimacy claims combined with earning claims is suspicious
        if results['fake_legitimacy'] and results['earning_claims']:
            score += 0.1
        elif results['fake_legitimacy']:
            score += min(0.1, len(results['fake_legitimacy']) * 0.03)
        
        return min(1.0, score)
    
    @classmethod
    def get_pattern_report(cls, detection_results: Dict) -> str:
        """
        Generate a human-readable report of detected patterns.
        
        Args:
            detection_results: Results from detect_patterns()
            
        Returns:
            Formatted report string
        """
        report = []
        report.append(f"🔍 Pattern Detection Report")
        report.append(f"Risk Level: {detection_results['risk_level']} ({detection_results['risk_score']:.1%})")
        
        if detection_results['earning_claims']:
            report.append(f"\n💰 Earning Claims Detected ({len(detection_results['earning_claims'])}):")
            for claim in detection_results['earning_claims'][:5]:  # Show top 5
                report.append(f"  • {claim['match'][:70]}")
        
        if detection_results['testimonial_clustering']['is_clustered']:
            report.append(f"\n👥 Fake Testimonial Clustering Detected:")
            tc = detection_results['testimonial_clustering']
            report.append(f"  • {tc['testimonial_count']} named testimonials found")
            report.append(f"  • {tc['fake_phrase_count']} suspicious phrases detected")
        
        if detection_results['urgency_tactics']:
            report.append(f"\n⏰ Urgency Tactics Detected ({len(detection_results['urgency_tactics'])}):")
            for tactic in detection_results['urgency_tactics'][:3]:
                report.append(f"  • {tactic['match'][:70]}")
        
        if detection_results['fake_legitimacy']:
            report.append(f"\n✓ False Legitimacy Claims ({len(detection_results['fake_legitimacy'])}):")
            for claim in detection_results['fake_legitimacy'][:3]:
                report.append(f"  • {claim['match'][:70]}")
        
        if detection_results['flagged']:
            report.append(f"\n🚨 FLAGGED AS POTENTIAL SCAM")
        
        return '\n'.join(report)

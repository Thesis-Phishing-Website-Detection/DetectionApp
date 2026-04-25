"""
Crypto phishing and gambling website detector.
Rule-based detection for specific phishing categories that the model may miss.
"""
import re
import logging
from typing import Dict, List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CryptoGamblingDetector:
    """Detects crypto phishing and gambling/betting scams using keyword and pattern analysis."""
    
    # Crypto phishing indicators
    CRYPTO_PHISHING_KEYWORDS = {
        # Wallet/seed phrases
        'seed phrase', 'private key', 'recovery phrase', 'mnemonic',
        'wallet address', 'wallet import', 'import wallet', 'wallet backup',
        
        # Crypto exchanges (fake clones)
        'binance', 'coinbase', 'kraken', 'huobi', 'kucoin', 'bybit',
        'metamask', 'wallet connect', 'ledger live', 'trezor',
        
        # Mining/staking scams
        'hash rate', 'mining pool', 'hashpower', 'cloud mining',
        'stake rewards', 'yield farming', 'liquidity mining',
        'passive income', 'guaranteed returns', 'daily returns',
        
        # Pump & dump / Investment scams
        'guaranteed profit', 'guaranteed returns', 'risk free',
        'limited time offer', 'exclusive opportunity', 'double your bitcoin',
        'multiply your crypto', 'instant profit', 'get rich quick',
        
        # Recovery scams
        'recover your funds', 'recover lost bitcoin', 'fund recovery',
        'claim your coins', 'airdrop claim', 'unclaimed tokens',
        
        # Fake verification
        'verify wallet', 'verify account', 'connect wallet', 'authenticate wallet',
        'validate transaction', 'confirm transaction', 'transaction pending',
        
        # Token/coin names (commonly used in scams)
        'dogecoin', 'shiba inu', 'safemoon', 'doge', 'shib',
    }
    
    # Gambling/betting website indicators
    GAMBLING_KEYWORDS = {
        # Sports betting
        'sports betting', 'sportsbook', 'sports wager', 'live betting',
        'football betting', 'soccer betting', 'nba betting', 'nfl betting',
        'odds', 'handicap', 'parlay', 'moneyline',
        
        # Casino/slots
        'casino', 'slot machine', 'slots', 'roulette', 'blackjack',
        'poker room', 'card game', 'table games', 'live dealer',
        
        # Lotteries/raffles
        'lottery', 'lottery ticket', 'lotto', 'raffle', 'sweepstakes',
        'instant win', 'scratch card', 'daily draw', 'jackpot',
        
        # Betting/wagering
        'place bet', 'wager', 'betting odds', 'betting slip',
        'accumulator', 'bet slip', 'live wager', 'in-play betting',
        
        # Crypto gambling (increasingly common)
        'crypto casino', 'bitcoin betting', 'ethereum gambling',
        'crypto slots', 'dice game', 'provably fair',
        
        # Fantasy sports
        'fantasy sports', 'daily fantasy', 'dfs', 'fantasy football',
        'fantasy basketball', 'fantasy baseball',
        
        # High-risk indicators
        'minimum deposit', 'welcome bonus', 'bonus code', 'free spins',
        'match bonus', 'cashback', 'no deposit bonus', 'deposit bonus',
    }
    
    # Suspicious domain patterns
    SUSPICIOUS_DOMAIN_PATTERNS = {
        # Homograph attacks / look-alikes
        r'b1t.*hash', r'bithash', r'bit\-hash', r'bit_hash',
        r'binance.*clone', r'fake.*binance', r'binance.*fake',
        r'metamask.*clone', r'fake.*metamask',
        r'coinbase.*clone', r'fake.*coinbase',
        
        # Free domains commonly used for phishing
        r'\.tk$', r'\.ml$', r'\.ga$', r'\.cf$',
        r'\.github\.io$', r'\.herokuapp\.com$', r'\.repl\.co$',
        
        # Suspicious TLDs
        r'\.vip$', r'\.top$', r'\.loan$', r'\.science$',
        r'\.win$', r'\.bid$', r'\.trade$',
    }
    
    @staticmethod
    def check_crypto_phishing(text: str, url: str = "") -> Tuple[bool, Dict]:
        """
        Check if content indicates crypto phishing.
        
        Args:
            text: Website text content
            url: Website URL (optional, for domain analysis)
            
        Returns:
            Tuple of (is_crypto_phishing, details_dict)
        """
        text_lower = text.lower()
        details = {
            'is_crypto_phishing': False,
            'confidence': 0,
            'detected_keywords': [],
            'risk_factors': [],
            'evidence_count': 0
        }
        
        # Check for crypto phishing keywords
        found_keywords = []
        for keyword in CryptoGamblingDetector.CRYPTO_PHISHING_KEYWORDS:
            if keyword in text_lower:
                # Count occurrences for confidence
                count = text_lower.count(keyword)
                found_keywords.append((keyword, count))
                details['evidence_count'] += count
        
        details['detected_keywords'] = found_keywords
        
        # Check suspicious domain patterns
        domain_risks = []
        if url:
            url_lower = url.lower()
            for pattern in CryptoGamblingDetector.SUSPICIOUS_DOMAIN_PATTERNS:
                if re.search(pattern, url_lower):
                    domain_risks.append(pattern)
                    details['evidence_count'] += 2  # Domain is strong evidence
            details['risk_factors'].extend(domain_risks)
        
        # Red flags for crypto scams
        red_flags = [
            ('guaranteed.*returns?', 'Promises guaranteed returns'),
            ('risk.*free', 'Claims risk-free investment'),
            ('limited.*time.*offer', 'Limited time offers pressure users'),
            ('act.*now', 'Urgency tactics (act now)'),
            (r'\b\d+%.*profit\b', 'Claims high profit percentages'),
            (r'double.*money|double.*bitcoin', 'Promise to double money'),
            (r'claim.*reward|claim.*bonus', 'False claim/bonus promises'),
        ]
        
        for pattern, description in red_flags:
            if re.search(pattern, text_lower):
                details['risk_factors'].append(description)
                details['evidence_count'] += 2
        
        # Calculate confidence
        # Keywords: 1 point each, Domain risks: 2 points each, Red flags: 2 points each
        max_evidence = len(CryptoGamblingDetector.CRYPTO_PHISHING_KEYWORDS)
        details['confidence'] = min(100, (details['evidence_count'] / max_evidence) * 100)
        
        # Threshold: if we have multiple indicators, flag as crypto phishing
        details['is_crypto_phishing'] = (
            details['evidence_count'] >= 5 or  # Multiple keyword hits
            (details['evidence_count'] >= 3 and domain_risks) or  # Keywords + suspicious domain
            len(domain_risks) >= 2  # Multiple domain red flags
        )
        
        return details['is_crypto_phishing'], details
    
    @staticmethod
    def check_gambling(text: str, url: str = "") -> Tuple[bool, Dict]:
        """
        Check if content indicates gambling/betting website.
        
        Args:
            text: Website text content
            url: Website URL (optional)
            
        Returns:
            Tuple of (is_gambling, details_dict)
        """
        text_lower = text.lower()
        details = {
            'is_gambling': False,
            'confidence': 0,
            'detected_keywords': [],
            'gambling_type': [],
            'evidence_count': 0
        }
        
        # Check for gambling keywords
        found_keywords = []
        gambling_types = set()
        
        for keyword in CryptoGamblingDetector.GAMBLING_KEYWORDS:
            if keyword in text_lower:
                count = text_lower.count(keyword)
                found_keywords.append((keyword, count))
                details['evidence_count'] += count
                
                # Categorize gambling type
                if any(x in keyword for x in ['casino', 'slot', 'roulette', 'blackjack', 'poker']):
                    gambling_types.add('Casino/Slots')
                elif any(x in keyword for x in ['betting', 'odds', 'wager', 'parlay', 'handicap']):
                    gambling_types.add('Sports Betting')
                elif any(x in keyword for x in ['lottery', 'lotto', 'raffle', 'jackpot']):
                    gambling_types.add('Lottery/Raffle')
                elif any(x in keyword for x in ['fantasy', 'dfs']):
                    gambling_types.add('Fantasy Sports')
                elif any(x in keyword for x in ['crypto', 'bitcoin']):
                    gambling_types.add('Crypto Gambling')
        
        details['detected_keywords'] = found_keywords
        details['gambling_type'] = list(gambling_types)
        
        # Gambling marketing tactics
        marketing_patterns = [
            (r'welcome.*bonus|bonus.*code', 'Welcome/signup bonus'),
            (r'no.*deposit.*bonus|free.*spins', 'No deposit bonus offers'),
            (r'match.*bonus|deposit.*bonus', 'Deposit matching bonus'),
            (r'cashback|money.*back', 'Cashback offers'),
            (r'vip.*program|loyalty.*program', 'VIP/loyalty programs'),
        ]
        
        marketing_count = 0
        for pattern, description in marketing_patterns:
            if re.search(pattern, text_lower):
                details['evidence_count'] += 1
                marketing_count += 1
        
        # Calculate confidence
        details['confidence'] = min(100, (details['evidence_count'] / 10) * 100)
        
        # Threshold: flag if we have multiple gambling indicators
        details['is_gambling'] = (
            details['evidence_count'] >= 3 or
            (len(gambling_types) >= 1 and marketing_count >= 2)
        )
        
        return details['is_gambling'], details
    
    @staticmethod
    def detect(text: str, url: str = "") -> Dict:
        """
        Comprehensive detection for crypto phishing and gambling sites.
        
        Args:
            text: Website text content
            url: Website URL
            
        Returns:
            Dictionary with detection results
        """
        logger.info("Running crypto/gambling phishing detection...")
        
        is_crypto, crypto_details = CryptoGamblingDetector.check_crypto_phishing(text, url)
        is_gambling, gambling_details = CryptoGamblingDetector.check_gambling(text, url)
        
        result = {
            'crypto_phishing': {
                'detected': is_crypto,
                'details': crypto_details
            },
            'gambling': {
                'detected': is_gambling,
                'details': gambling_details
            },
            'overall_risk': 'HIGH' if (is_crypto or is_gambling) else 'NORMAL'
        }
        
        if is_crypto:
            logger.warning(f"Crypto phishing detected with {crypto_details['confidence']:.1f}% confidence")
        if is_gambling:
            logger.warning(f"Gambling website detected with {gambling_details['confidence']:.1f}% confidence")
        
        return result

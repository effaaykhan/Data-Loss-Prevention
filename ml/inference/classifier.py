"""
ML-Based DLP Classifier
Hybrid classification using regex, fingerprinting, entropy, and ML models
"""

import re
import hashlib
import math
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class DLPClassifier:
    """
    Hybrid DLP classifier combining deterministic and ML-based methods
    """

    def __init__(self):
        self.regex_patterns = self._load_regex_patterns()
        self.fingerprints = set()  # SHA256 hashes of known sensitive docs
        self.ml_model = None  # Placeholder for ML model

    def _load_regex_patterns(self) -> Dict[str, List[re.Pattern]]:
        """
        Load regex patterns for deterministic detection
        """
        return {
            'PAN': [
                # Visa
                re.compile(r'\b4[0-9]{12}(?:[0-9]{3})?\b'),
                # Mastercard
                re.compile(r'\b5[1-5][0-9]{14}\b'),
                # Amex
                re.compile(r'\b3[47][0-9]{13}\b'),
                # Discover
                re.compile(r'\b6(?:011|5[0-9]{2})[0-9]{12}\b'),
            ],
            'SSN': [
                # US Social Security Number
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                re.compile(r'\b\d{9}\b'),
            ],
            'EMAIL': [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            ],
            'PHONE': [
                # US Phone
                re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
                # International
                re.compile(r'\+\d{1,3}[-.]?\d{1,14}\b'),
            ],
            'API_KEY': [
                # AWS
                re.compile(r'AKIA[0-9A-Z]{16}'),
                # Generic API key patterns
                re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{32,})["\']?', re.I),
            ],
            'SECRET': [
                re.compile(r'secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?', re.I),
                re.compile(r'password["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-!@#$%^&*]{8,})["\']?', re.I),
            ],
            'IP_ADDRESS': [
                re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
            ],
            # Indian identifiers
            'AADHAAR': [
                re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
                re.compile(r'\b\d{12}\b'),
            ],
            'PAN_INDIA': [
                re.compile(r'\b[A-Z]{5}\d{4}[A-Z]{1}\b'),
            ],
            'IFSC': [
                re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b'),
            ],
            'INDIAN_BANK_ACCOUNT': [
                re.compile(r'\b\d{9,18}\b'),
            ],
            'INDIAN_PHONE': [
                re.compile(r'\b(\+91|91|0)?[6-9]\d{9}\b'),
                re.compile(r'\b(\+91|91|0)?[1-9]\d{9}\b'),
            ],
            'UPI_ID': [
                re.compile(r'\b[\w.-]+@(paytm|phonepe|ybl|okaxis|okhdfcbank|oksbi|okicici)\b'),
            ],
            'MICR': [
                re.compile(r'\b\d{9}\b'),
            ],
            'INDIAN_DOB': [
                re.compile(r'\b(0[1-9]|[12][0-9]|3[01])[/-](0[1-9]|1[0-2])[/-](19|20)\d{2}\b'),
            ],
            # Source code detection
            'SOURCE_CODE': [
                re.compile(r'\b(function|def|class|public|private|protected|static)\s+\w+'),
                re.compile(r'\b(import|from|require|include|using|package)\s+'),
                re.compile(r'\b(const|let|var|int|string|float|bool)\s+\w+\s*='),
            ],
            'API_KEY_IN_CODE': [
                re.compile(r'AKIA[0-9A-Z]{16}'),
                re.compile(r'ghp_[A-Za-z0-9]{36}'),
                re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{32,})["\']?', re.I),
            ],
            'DATABASE_CONNECTION': [
                re.compile(r'jdbc:(mysql|postgresql|oracle|sqlserver)://'),
                re.compile(r'mongodb://'),
                re.compile(r'mongodb\+srv://'),
                re.compile(r'redis://'),
                re.compile(r'rediss://'),
            ],
        }

    def classify(self, content: str) -> Dict[str, Any]:
        """
        Classify content using hybrid approach

        Args:
            content: Text content to classify

        Returns:
            Classification result
        """
        scores = []
        labels = []
        methods = []

        # 1. Fingerprint matching (exact match)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if content_hash in self.fingerprints:
            scores.append(1.0)
            labels.append('KNOWN_SENSITIVE_DOC')
            methods.append('fingerprint')

        # 2. Regex pattern matching
        regex_score, regex_labels = self._regex_detection(content)
        if regex_score > 0:
            scores.append(regex_score)
            labels.extend(regex_labels)
            methods.append('regex')

        # 3. Entropy analysis
        entropy = self._calculate_entropy(content)
        if entropy > 3.5:
            scores.append(0.7)
            labels.append('HIGH_ENTROPY')
            methods.append('entropy')

        # 4. ML model inference (if available)
        if self.ml_model:
            ml_score, ml_label = self._ml_inference(content)
            if ml_score > 0.75:
                scores.append(ml_score * 0.8)
                labels.append(ml_label)
                methods.append('ml')

        # Calculate final score
        final_score = min(max(scores) if scores else 0.0, 1.0)
        confidence = self._calculate_confidence(scores, labels)

        return {
            'score': final_score,
            'labels': list(set(labels)),  # Remove duplicates
            'methods': ','.join(set(methods)),
            'confidence': confidence,
            'entropy': entropy,
        }

    def _regex_detection(self, content: str) -> Tuple[float, List[str]]:
        """
        Detect patterns using regex

        Args:
            content: Text content

        Returns:
            Tuple of (score, labels)
        """
        labels = []
        match_counts = {}

        for label, patterns in self.regex_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                if matches:
                    # Validate matches
                    if label == 'PAN' and not all(self._validate_luhn(m) for m in matches if m.replace('-', '').isdigit()):
                        continue

                    match_counts[label] = match_counts.get(label, 0) + len(matches)
                    if label not in labels:
                        labels.append(label)

        # Calculate score based on match density
        if not labels:
            return 0.0, []

        max_count = max(match_counts.values())
        score = min(0.9 * (max_count / 5), 0.95)  # Scale by count, cap at 0.95

        return score, labels

    def _validate_luhn(self, card_number: str) -> bool:
        """
        Validate credit card using Luhn algorithm

        Args:
            card_number: Card number string

        Returns:
            True if valid
        """
        try:
            digits = [int(d) for d in card_number if d.isdigit()]
            checksum = 0

            for i, digit in enumerate(reversed(digits)):
                if i % 2 == 1:
                    digit *= 2
                    if digit > 9:
                        digit -= 9
                checksum += digit

            return checksum % 10 == 0
        except:
            return False

    def _calculate_entropy(self, content: str) -> float:
        """
        Calculate Shannon entropy of content

        Args:
            content: Text content

        Returns:
            Entropy value
        """
        if not content:
            return 0.0

        # Count character frequencies
        freq = {}
        for char in content:
            freq[char] = freq.get(char, 0) + 1

        # Calculate entropy
        length = len(content)
        entropy = 0.0

        for count in freq.values():
            probability = count / length
            entropy -= probability * math.log2(probability)

        return entropy

    def _calculate_confidence(self, scores: List[float], labels: List[str]) -> float:
        """
        Calculate confidence in classification

        Args:
            scores: List of scores from different methods
            labels: List of detected labels

        Returns:
            Confidence value (0.0 to 1.0)
        """
        if not scores:
            return 0.0

        # Confidence increases with:
        # 1. Higher scores
        # 2. Multiple detection methods
        # 3. Consistent labels

        avg_score = sum(scores) / len(scores)
        method_count = len(scores)
        label_consistency = 1.0 / (1.0 + len(set(labels)) * 0.1)

        confidence = avg_score * (0.7 + 0.15 * min(method_count, 3) / 3) * label_consistency

        return min(confidence, 1.0)

    def _ml_inference(self, content: str) -> Tuple[float, str]:
        """
        Run ML model inference (placeholder)

        Args:
            content: Text content

        Returns:
            Tuple of (score, label)
        """
        # TODO: Implement ML model inference
        # This would use a trained model (BERT, etc.) for classification
        return 0.0, ''

    def add_fingerprint(self, content: str) -> None:
        """
        Add content fingerprint to known sensitive documents

        Args:
            content: Content to fingerprint
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        self.fingerprints.add(content_hash)
        logger.info(f"Added fingerprint: {content_hash[:16]}...")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    classifier = DLPClassifier()

    # Test with credit card
    test_content_1 = "Please process payment for card 4532015112830366"
    result_1 = classifier.classify(test_content_1)
    print(f"Result 1: {result_1}")

    # Test with SSN
    test_content_2 = "Employee SSN: 123-45-6789, DOB: 01/15/1980"
    result_2 = classifier.classify(test_content_2)
    print(f"Result 2: {result_2}")

    # Test with API key (FAKE KEY FOR TESTING ONLY)
    test_content_3 = 'API_KEY="sk_test_FAKE1234567890abcdefghijklmnop"'
    result_3 = classifier.classify(test_content_3)
    print(f"Result 3: {result_3}")

    # Test with high entropy (encrypted data)
    test_content_4 = "aW50ZWdyYXRlZA=="
    result_4 = classifier.classify(test_content_4)
    print(f"Result 4: {result_4}")

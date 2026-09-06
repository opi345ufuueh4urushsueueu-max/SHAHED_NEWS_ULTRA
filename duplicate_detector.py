"""
SHAHED NEWS ULTRA - Duplicate Detection
"""

import hashlib
import re
from typing import Tuple
from logger import logger


class DuplicateDetector:
    """Advanced duplicate detection system"""

    @staticmethod
    def calculate_hashes(text: str) -> Tuple[str, str]:
        """Calculate both raw and normalized text hashes"""
        # Raw SHA-256 hash
        raw_hash = hashlib.sha256(text.encode()).hexdigest()

        # Normalized hash (for semantic similarity)
        normalized = DuplicateDetector.normalize_text(text)
        normalized_hash = hashlib.sha256(normalized.encode()).hexdigest()

        return raw_hash, normalized_hash

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for duplicate detection"""
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)

        # Remove special characters but keep Persian/Arabic
        text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)

        # Remove extra spaces again
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def is_similar(text1: str, text2: str, threshold: float = 0.85) -> bool:
        """Check if two texts are similar using Jaccard similarity"""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())

        if not set1 or not set2:
            return False

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text without changing meaning"""
        # Fix extra spaces
        text = re.sub(r'\s+', ' ', text)

        # Fix spaces around punctuation
        text = re.sub(r'\s+([.،؛:؟!])', r'\1', text)
        text = re.sub(r'([.،؛:؟!])\s+', r'\1 ', text)

        # Remove excessive empty lines
        text = re.sub(r'\n\n+', '\n', text)

        return text.strip()

    @staticmethod
    def detect_breaking_news(text: str) -> bool:
        """Detect if text contains breaking news keywords"""
        breaking_keywords = [
            'فوری',
            'خبر فوری',
            'لحظه‌ای',
            'مهم',
            'breaking',
            'breaking news',
            '🚨',
            '⚠️',
            'urgent',
            'اورژانسی'
        ]

        text_lower = text.lower()
        for keyword in breaking_keywords:
            if keyword.lower() in text_lower:
                logger.debug(f"Breaking news detected: {keyword}")
                return True

        return False

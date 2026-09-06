"""
SHAHED NEWS ULTRA - Text Processor
"""

import re
from typing import List
from logger import logger
from duplicate_detector import DuplicateDetector


class TextProcessor:
    """Text processing and cleaning"""

    @staticmethod
    def process_text(text: str) -> str:
        """Process and clean text while preserving meaning"""
        if not text:
            return ""

        # Clean text
        text = DuplicateDetector.clean_text(text)

        # Remove excessive punctuation
        text = re.sub(r'([.،؛:؟!])\1{2,}', r'\1', text)

        return text.strip()

    @staticmethod
    def split_message(text: str, max_length: int = 4096) -> List[str]:
        """Split long message into parts"""
        if len(text) <= max_length:
            return [text]

        parts = []
        lines = text.split('\n')
        current_part = ""

        for line in lines:
            if len(current_part) + len(line) + 1 > max_length:
                if current_part:
                    parts.append(current_part)
                current_part = line
            else:
                current_part += ('\n' + line) if current_part else line

        if current_part:
            parts.append(current_part)

        return parts if parts else [text[:max_length]]

    @staticmethod
    def format_for_publishing(
        source_name: str,
        text: str,
        link: str = None,
        is_breaking: bool = False
    ) -> List[str]:
        """Format text for publishing"""
        formatted_parts = []

        # Breaking news header
        if is_breaking:
            header = "🚨 خبر فوری\n\n"
        else:
            header = ""

        # Source info
        source_header = f"📌 منبع: {source_name}\n━━━━━━━━━━━━━━━━\n\n"

        # Process and split text
        processed_text = TextProcessor.process_text(text)
        text_parts = TextProcessor.split_message(processed_text, max_length=3500)

        for idx, part in enumerate(text_parts):
            total = len(text_parts)

            # Build message
            message = ""
            if idx == 0:
                message += header + source_header

            # Add part info if multiple parts
            if total > 1:
                message += f"[قسمت {idx + 1}/{total}]\n\n"

            message += f"📰\n\n{part}\n\n"

            # Footer
            if idx == total - 1:
                message += "━━━━━━━━━━━━━━━━\n\n"
                message += "📡 شاهد نیوز\n"
                if link:
                    message += f"🔗 منبع اصلی: {link}"
                else:
                    message += "🔗 منبع اصلی: در دسترس نیست"

            formatted_parts.append(message)

        return formatted_parts

    @staticmethod
    def validate_text(text: str) -> bool:
        """Validate if text is meaningful"""
        if not text or len(text.strip()) < 10:
            return False

        # Check if text is mostly spam/advertisement
        if TextProcessor._is_spam(text):
            return False

        return True

    @staticmethod
    def _is_spam(text: str) -> bool:
        """Check if text is spam"""
        spam_keywords = [
            'آگهی',
            'تبلیغ',
            'خرید',
            'فروش',
            'قیمت',
            'discount',
            'sale',
            'buy',
        ]

        # Check for emoji spam
        emoji_count = len(re.findall(r'[\U0001F300-\U0001F9FF]', text))
        if emoji_count > 20:
            return True

        # Check for keyword spam
        text_lower = text.lower()
        spam_score = sum(1 for keyword in spam_keywords if keyword in text_lower)
        
        if spam_score > 3:
            return True

        return False

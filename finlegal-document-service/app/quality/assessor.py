import re

GARBAGE_PATTERNS = re.compile(r'(?:wVw|xnx|zFz|90KSX|32654|546632|99991|326654|KSX|EaV)', re.IGNORECASE)
SINGLE_CHAR_TOKENS = re.compile(r'(?:^|\s)[A-Za-z0-9$%&/+*:;\-.](?=\s|$)')
UNPRINTABLE_CHARS = re.compile(r'[\x00-\x08\x0E-\x1F\x7F-\x9F\uFFFD]')
OBSCURE_SYMBOLS = re.compile(r'[\u0250-\u036F\u0370-\u03FF\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF\u1D00-\u1E9F]')
NATURAL_WORDS = re.compile(r'\b[A-Za-z0-9\u00C0-\u1EF9]{3,}\b')
METADATA_STRINGS = re.compile(r'(?:https?://[^\s]+|\b(?:Adobe|UCS|Poppins|itfoundry|90KSX|EaV)\b)', re.IGNORECASE)

class QualityAssessor:
    @staticmethod
    def assess_page_quality(text: str) -> float:
        """
        Calculates text quality score between 0.00 (complete font garbage) and 1.00 (perfect natural text).
        """
        if not text or not text.strip():
            return 0.0

        sample = text[:1500].strip()
        sample_len = max(1, len(sample))

        # 1. Explicit check for font vector path garbage tokens (wVw, xnx, zFz, etc.)
        if GARBAGE_PATTERNS.search(sample):
            return 0.15

        # 2. Check for high ratio of single-character CID tokens
        single_chars = len(SINGLE_CHAR_TOKENS.findall(sample))
        total_tokens = max(1, len(sample.split()))
        single_ratio = single_chars / total_tokens
        if single_ratio > 0.22:
            return max(0.10, 1.0 - (single_ratio * 2.5))

        # 3. Check for natural words (excluding metadata URLs and font strings)
        clean_sample = METADATA_STRINGS.sub('', sample)
        real_words = NATURAL_WORDS.findall(clean_sample)
        
        if len(real_words) < 6:
            return 0.30

        # 4. Check unprintable control characters
        unprintable = len(UNPRINTABLE_CHARS.findall(sample))
        if (unprintable / sample_len) > 0.08:
            return 0.20

        # 5. Check obscure symbols
        obscure = len(OBSCURE_SYMBOLS.findall(sample))
        if obscure >= 5:
            return 0.25

        # High quality natural language text
        word_count_bonus = min(0.30, len(real_words) * 0.01)
        score = min(1.00, 0.70 + word_count_bonus - (single_ratio * 0.5))
        return round(max(0.0, score), 2)

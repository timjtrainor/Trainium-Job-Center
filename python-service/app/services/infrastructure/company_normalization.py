"""
Company name normalization service for deduplication.

Handles common variations, aliases, subsidiaries, and legal entities
to ensure cross-site job deduplication works correctly.
"""
import re
from typing import Optional, Dict, Set
from loguru import logger


class CompanyNormalizer:
    """
    Normalizes company names to canonical forms for deduplication.

    Handles:
    - Legal entity suffixes (Inc, LLC, Corp, etc.)
    - Known aliases and acquisitions (AWS → Amazon, Meta → Facebook)
    - Common abbreviations and variations
    - Domain-based matching (.com, Inc. vs base name)
    """

    # Known company aliases and subsidiaries
    # Format: {alias: canonical_name}
    COMPANY_ALIASES = {
        # Amazon family
        "amazon": "amazon",
        "amazon.com": "amazon",
        "amazoncom": "amazon",
        "aws": "amazon",
        "amazon web services": "amazon",
        "whole foods": "amazon",
        "whole foods market": "amazon",
        "audible": "amazon",
        "zappos": "amazon",
        "twitch": "amazon",

        # Microsoft family
        "microsoft": "microsoft",
        "msft": "microsoft",
        "microsoft corporation": "microsoft",
        "azure": "microsoft",
        "github": "microsoft",
        "linkedin": "microsoft",  # Owned by Microsoft but often listed separately
        "xbox": "microsoft",

        # Google/Alphabet family
        "google": "google",
        "alphabet": "google",
        "youtube": "google",
        "google cloud": "google",
        "gcp": "google",
        "waymo": "google",
        "verily": "google",

        # Meta family
        "meta": "meta",
        "facebook": "meta",
        "instagram": "meta",
        "whatsapp": "meta",

        # Apple
        "apple": "apple",
        "apple inc": "apple",

        # Salesforce family
        "salesforce": "salesforce",
        "slack": "salesforce",
        "tableau": "salesforce",
        "mulesoft": "salesforce",

        # Other major tech
        "netflix": "netflix",
        "uber": "uber",
        "uber technologies": "uber",
        "lyft": "lyft",
        "airbnb": "airbnb",
        "spotify": "spotify",
        "stripe": "stripe",
        "square": "block",  # Renamed to Block
        "block": "block",
        "cash app": "block",

        # Boeing family (for Seattle relevance)
        "boeing": "boeing",
        "boeing company": "boeing",

        # Oracle family
        "oracle": "oracle",
        "oracle corporation": "oracle",

        # Adobe
        "adobe": "adobe",
        "adobe systems": "adobe",

        # IBM
        "ibm": "ibm",
        "international business machines": "ibm",
        "red hat": "ibm",

        # Snowflake
        "snowflake": "snowflake",
        "snowflake computing": "snowflake",

        # Databricks
        "databricks": "databricks",

        # Add more as you discover duplicates
    }

    # Legal entity suffixes to remove
    # NOTE: Only remove actual legal suffixes, NOT business descriptors like "tech" or "systems"
    # which are often part of the actual company name
    LEGAL_SUFFIXES = [
        r'\binc\.?\b',
        r'\bincorporated\b',
        r'\bllc\.?\b',
        r'\bltd\.?\b',
        r'\blimited\b',
        r'\bcorp\.?\b',
        r'\bcorporation\b',
        r'\bcompany\b',
        r'\bco\.?\b',
        r'\bplc\.?\b',
        r'\blp\.?\b',
        r'\bllp\.?\b',
    ]

    def __init__(self):
        """Initialize the normalizer with compiled regex patterns."""
        # Compile legal suffix patterns
        self.legal_suffix_pattern = re.compile(
            '|'.join(self.LEGAL_SUFFIXES),
            re.IGNORECASE
        )

    def normalize(self, company_name: str) -> str:
        """
        Normalize a company name to its canonical form.

        Args:
            company_name: Raw company name from job posting

        Returns:
            Normalized canonical company name

        Examples:
            "Amazon Web Services, Inc." → "amazon"
            "Microsoft Corporation" → "microsoft"
            "Meta Platforms, Inc." → "meta"
        """
        if not company_name:
            return ""

        # Step 1: Basic cleaning
        normalized = company_name.lower().strip()

        # Remove common punctuation and extra whitespace
        normalized = re.sub(r'[,\.]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Step 2: Remove legal entity suffixes
        normalized = self.legal_suffix_pattern.sub('', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Step 3: Check known aliases
        # Try exact match first
        if normalized in self.COMPANY_ALIASES:
            return self.COMPANY_ALIASES[normalized]

        # Try removing spaces for multi-word companies
        normalized_no_spaces = normalized.replace(' ', '')
        if normalized_no_spaces in self.COMPANY_ALIASES:
            return self.COMPANY_ALIASES[normalized_no_spaces]

        # Step 4: Check for partial matches (for "Google LLC" → "google")
        for alias, canonical in self.COMPANY_ALIASES.items():
            if alias in normalized or normalized in alias:
                # Verify it's a word boundary match to avoid false positives
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, normalized):
                    return canonical

        # Step 5: Final cleanup - remove remaining special chars
        normalized = re.sub(r'[^a-z0-9\s]+', '', normalized)
        normalized = re.sub(r'\s+', '', normalized)  # Remove all spaces

        return normalized

    def add_alias(self, alias: str, canonical_name: str) -> None:
        """
        Add a new company alias mapping.

        Useful for discovering new duplicates during operation.

        Args:
            alias: Company name variation to normalize
            canonical_name: The canonical name to map to
        """
        normalized_alias = alias.lower().strip()
        self.COMPANY_ALIASES[normalized_alias] = canonical_name.lower()
        logger.info(f"Added company alias: {alias} → {canonical_name}")

    def get_aliases_for(self, canonical_name: str) -> Set[str]:
        """
        Get all known aliases for a canonical company name.

        Args:
            canonical_name: The canonical company name

        Returns:
            Set of all known aliases that map to this canonical name
        """
        canonical_lower = canonical_name.lower()
        return {
            alias for alias, canonical in self.COMPANY_ALIASES.items()
            if canonical == canonical_lower
        }


# Singleton instance
_normalizer_instance: Optional[CompanyNormalizer] = None


def get_company_normalizer() -> CompanyNormalizer:
    """Get or create the singleton CompanyNormalizer instance."""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = CompanyNormalizer()
    return _normalizer_instance


def normalize_company_name(company_name: str) -> str:
    """
    Convenience function to normalize a company name.

    Args:
        company_name: Raw company name from job posting

    Returns:
        Normalized canonical company name
    """
    normalizer = get_company_normalizer()
    return normalizer.normalize(company_name)

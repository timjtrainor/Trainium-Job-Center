"""
Tests for company name normalization service.
"""
import pytest
from app.services.infrastructure.company_normalization import (
    CompanyNormalizer,
    normalize_company_name,
    get_company_normalizer
)


class TestCompanyNormalizer:
    """Test cases for CompanyNormalizer."""

    def test_amazon_variations(self):
        """Test that all Amazon variations normalize correctly."""
        normalizer = CompanyNormalizer()

        amazon_variations = [
            "Amazon",
            "Amazon.com",
            "Amazon, Inc.",
            "Amazon.com, Inc.",
            "AWS",
            "Amazon Web Services",
            "Amazon Web Services, Inc.",
            "AMAZON",
            "amazon.com",
        ]

        for variation in amazon_variations:
            result = normalizer.normalize(variation)
            assert result == "amazon", f"Failed for {variation}: got {result}"

    def test_microsoft_variations(self):
        """Test Microsoft and subsidiaries."""
        normalizer = CompanyNormalizer()

        microsoft_variations = [
            "Microsoft",
            "Microsoft Corporation",
            "MSFT",
            "Microsoft Corp",
            "Azure",
            "GitHub",
        ]

        for variation in microsoft_variations:
            result = normalizer.normalize(variation)
            assert result == "microsoft", f"Failed for {variation}: got {result}"

    def test_google_alphabet_variations(self):
        """Test Google/Alphabet family."""
        normalizer = CompanyNormalizer()

        google_variations = [
            "Google",
            "Google LLC",
            "Alphabet",
            "Alphabet Inc.",
            "Google Cloud",
            "YouTube",
            "GCP",
        ]

        for variation in google_variations:
            result = normalizer.normalize(variation)
            assert result == "google", f"Failed for {variation}: got {result}"

    def test_meta_facebook_variations(self):
        """Test Meta/Facebook rebranding."""
        normalizer = CompanyNormalizer()

        meta_variations = [
            "Meta",
            "Meta Platforms",
            "Meta Platforms, Inc.",
            "Facebook",
            "Facebook, Inc.",
            "Instagram",
            "WhatsApp",
        ]

        for variation in meta_variations:
            result = normalizer.normalize(variation)
            assert result == "meta", f"Failed for {variation}: got {result}"

    def test_salesforce_acquisitions(self):
        """Test Salesforce and acquired companies."""
        normalizer = CompanyNormalizer()

        salesforce_variations = [
            "Salesforce",
            "Salesforce.com",
            "Salesforce, Inc.",
            "Slack",
            "Slack Technologies",
            "Tableau",
            "MuleSoft",
        ]

        for variation in salesforce_variations:
            result = normalizer.normalize(variation)
            assert result == "salesforce", f"Failed for {variation}: got {result}"

    def test_legal_entity_removal(self):
        """Test that legal suffixes are properly removed."""
        normalizer = CompanyNormalizer()

        test_cases = [
            ("Acme Corp", "acme"),
            ("Acme Corporation", "acme"),
            ("Acme Inc.", "acme"),
            ("Acme LLC", "acme"),
            ("Acme Co.", "acme"),
            ("Acme Company", "acme"),
        ]

        for input_name, expected in test_cases:
            result = normalizer.normalize(input_name)
            assert result == expected, f"Failed for {input_name}: got {result}, expected {expected}"

    def test_unknown_company(self):
        """Test handling of companies not in the alias map."""
        normalizer = CompanyNormalizer()

        # Should normalize to clean form even if not in alias map
        result = normalizer.normalize("Random Startup, Inc.")
        assert result == "randomstartup"

        # "Tech" is preserved, "Company" and "LLC" are legal suffixes and removed
        result = normalizer.normalize("Tech Company LLC")
        assert result == "tech"

        # Test a company name with "tech" as part of the name
        result = normalizer.normalize("TechCorp LLC")
        assert result == "techcorp"

    def test_case_insensitivity(self):
        """Test that normalization is case-insensitive."""
        normalizer = CompanyNormalizer()

        assert normalizer.normalize("AMAZON") == "amazon"
        assert normalizer.normalize("amazon") == "amazon"
        assert normalizer.normalize("AmAzOn") == "amazon"

    def test_whitespace_handling(self):
        """Test proper handling of whitespace."""
        normalizer = CompanyNormalizer()

        test_cases = [
            ("  Amazon  ", "amazon"),
            ("Amazon   Web   Services", "amazon"),
            ("Microsoft\t Corporation", "microsoft"),
        ]

        for input_name, expected in test_cases:
            result = normalizer.normalize(input_name)
            assert result == expected, f"Failed for '{input_name}': got {result}"

    def test_special_characters(self):
        """Test handling of special characters."""
        normalizer = CompanyNormalizer()

        test_cases = [
            ("Amazon.com, Inc.", "amazon"),
            ("Acme & Co.", "acme"),
            ("Tech-Company LLC", "techcompany"),
        ]

        for input_name, expected in test_cases:
            result = normalizer.normalize(input_name)
            assert result == expected, f"Failed for {input_name}: got {result}"

    def test_add_alias(self):
        """Test adding new aliases dynamically."""
        normalizer = CompanyNormalizer()

        # Add new alias
        normalizer.add_alias("NewCorp", "techgiant")

        # Should now normalize correctly
        assert normalizer.normalize("NewCorp") == "techgiant"
        assert normalizer.normalize("NewCorp Inc.") == "techgiant"

    def test_get_aliases_for(self):
        """Test retrieving all aliases for a canonical name."""
        normalizer = CompanyNormalizer()

        amazon_aliases = normalizer.get_aliases_for("amazon")

        # Should contain known Amazon aliases
        assert "aws" in amazon_aliases
        assert "amazon" in amazon_aliases
        assert "amazon web services" in amazon_aliases

    def test_empty_string(self):
        """Test handling of empty string."""
        normalizer = CompanyNormalizer()
        assert normalizer.normalize("") == ""
        assert normalizer.normalize("   ") == ""

    def test_singleton_instance(self):
        """Test that get_company_normalizer returns singleton."""
        normalizer1 = get_company_normalizer()
        normalizer2 = get_company_normalizer()

        assert normalizer1 is normalizer2

    def test_convenience_function(self):
        """Test the convenience function."""
        result = normalize_company_name("Amazon Web Services, Inc.")
        assert result == "amazon"


class TestRealWorldExamples:
    """Test cases with real-world job posting data."""

    def test_seattle_area_companies(self):
        """Test normalization for major Seattle-area employers."""
        normalizer = CompanyNormalizer()

        test_cases = [
            ("Amazon.com", "amazon"),
            ("Microsoft Corporation", "microsoft"),
            ("Boeing Company", "boeing"),
            ("The Boeing Company", "boeing"),
        ]

        for input_name, expected in test_cases:
            result = normalizer.normalize(input_name)
            assert result == expected, f"Failed for {input_name}: got {result}"

    def test_product_manager_focused_companies(self):
        """Test tech companies likely to post PM roles."""
        normalizer = CompanyNormalizer()

        test_cases = [
            ("Snowflake Computing", "snowflake"),
            ("Databricks", "databricks"),
            ("Stripe, Inc.", "stripe"),
            ("Airbnb, Inc.", "airbnb"),
            ("Uber Technologies", "uber"),
        ]

        for input_name, expected in test_cases:
            result = normalizer.normalize(input_name)
            assert result == expected, f"Failed for {input_name}: got {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

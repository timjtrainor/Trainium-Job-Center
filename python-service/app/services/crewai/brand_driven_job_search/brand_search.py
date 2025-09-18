"""
Brand search helper for ChromaDB career_brand collection queries.

This module provides functionality to extract career brand information
from ChromaDB and generate LinkedIn search queries based on brand dimensions.
"""
from typing import Dict, List, Any, Optional
from loguru import logger

from ..tools.chroma_search import chroma_search_tool


class BrandSearchHelper:
    """
    Helper class for querying career brand data from ChromaDB and
    generating LinkedIn search queries based on brand dimensions.
    """

    BRAND_SECTIONS = [
        "north_star_vision",
        "trajectory_mastery", 
        "values_compass",
        "lifestyle_alignment",
        "compensation_philosophy"
    ]

    def __init__(self):
        """Initialize the brand search helper."""
        self.collection_name = "career_brand"

    async def get_brand_section(self, section: str, user_id: str = None) -> Dict[str, Any]:
        """
        Retrieve a specific brand section from ChromaDB.
        
        Args:
            section: Brand section name (e.g., 'north_star_vision')
            user_id: Optional user ID for filtering
            
        Returns:
            Dictionary containing brand section data
        """
        try:
            # Create search query for the specific section
            search_query = f"section:{section}"
            if user_id:
                search_query += f" user_id:{user_id}"
            
            # Use the existing chroma search tool
            results = await chroma_search_tool(
                collection_name=self.collection_name,
                query_text=search_query,
                n_results=5,
                metadata_filter={"section": section} if not user_id else {"section": section, "user_id": user_id}
            )
            
            if not results or not results.get("documents"):
                logger.warning(f"No brand data found for section: {section}")
                return {"section": section, "content": "", "keywords": []}
            
            # Extract content and metadata
            documents = results["documents"][0] if isinstance(results["documents"][0], list) else [results["documents"][0]]
            metadatas = results.get("metadatas", [{}])[0] if results.get("metadatas") else [{}]
            
            content = " ".join(documents)
            
            return {
                "section": section,
                "content": content,
                "keywords": self._extract_keywords_from_content(content),
                "metadata": metadatas[0] if metadatas else {}
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve brand section {section}: {str(e)}")
            return {"section": section, "content": "", "keywords": []}

    def _extract_keywords_from_content(self, content: str) -> List[str]:
        """
        Extract relevant keywords from brand content for LinkedIn searches.
        
        Args:
            content: Brand section content text
            
        Returns:
            List of extracted keywords
        """
        if not content:
            return []
        
        # Simple keyword extraction - in practice, could use NLP libraries
        import re
        
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
            'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Extract words (alphanumeric, 3+ characters)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Filter out stop words and return unique keywords
        keywords = list(set(word for word in words if word not in stop_words))
        
        # Sort by relevance (could be improved with TF-IDF or similar)
        return sorted(keywords)[:10]  # Return top 10 keywords

    async def generate_search_queries(self, user_id: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Generate LinkedIn search queries based on all brand sections.
        
        Args:
            user_id: Optional user ID for personalized brand data
            
        Returns:
            Dictionary mapping brand sections to search query data
        """
        search_queries = {}
        
        for section in self.BRAND_SECTIONS:
            try:
                # Get brand section data
                brand_data = await self.get_brand_section(section, user_id)
                
                if not brand_data["content"]:
                    logger.warning(f"No content found for brand section: {section}")
                    continue
                
                # Generate search query based on section type
                query_data = self._generate_section_query(section, brand_data)
                search_queries[section] = query_data
                
            except Exception as e:
                logger.error(f"Failed to generate query for section {section}: {str(e)}")
                continue
        
        return search_queries

    def _generate_section_query(self, section: str, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a LinkedIn search query for a specific brand section.
        
        Args:
            section: Brand section name
            brand_data: Brand section data from ChromaDB
            
        Returns:
            Dictionary containing search query and metadata
        """
        keywords = brand_data.get("keywords", [])
        content = brand_data.get("content", "")
        
        # Customize search based on section type
        if section == "north_star_vision":
            # Focus on aspirational roles and industries
            search_terms = self._extract_vision_terms(keywords, content)
            job_types = ["full-time", "leadership"]
            
        elif section == "trajectory_mastery":
            # Focus on skill-based and growth roles
            search_terms = self._extract_skill_terms(keywords, content)
            job_types = ["full-time", "senior"]
            
        elif section == "values_compass":
            # Focus on company culture and values alignment
            search_terms = self._extract_values_terms(keywords, content)
            job_types = ["full-time"]
            
        elif section == "lifestyle_alignment":
            # Focus on work-life balance and location preferences
            search_terms = self._extract_lifestyle_terms(keywords, content)
            job_types = ["full-time", "remote", "hybrid"]
            
        elif section == "compensation_philosophy":
            # Focus on roles matching compensation expectations
            search_terms = self._extract_compensation_terms(keywords, content)
            job_types = ["full-time"]
            
        else:
            # Default case
            search_terms = keywords[:3] if keywords else []
            job_types = ["full-time"]
        
        return {
            "keywords": " ".join(search_terms),
            "search_terms": search_terms,
            "job_types": job_types,
            "section_content": content[:200] + "..." if len(content) > 200 else content,
            "brand_section": section,
            "total_keywords": len(keywords)
        }

    def _extract_vision_terms(self, keywords: List[str], content: str) -> List[str]:
        """Extract vision-focused search terms."""
        vision_terms = [k for k in keywords if any(v in k for v in ['lead', 'direct', 'manage', 'strategy', 'vision'])]
        return vision_terms[:3] if vision_terms else keywords[:3]

    def _extract_skill_terms(self, keywords: List[str], content: str) -> List[str]:
        """Extract skill-focused search terms."""
        skill_terms = [k for k in keywords if any(s in k for s in ['engineer', 'develop', 'design', 'analy', 'techni'])]
        return skill_terms[:3] if skill_terms else keywords[:3]

    def _extract_values_terms(self, keywords: List[str], content: str) -> List[str]:
        """Extract values-focused search terms.""" 
        values_terms = [k for k in keywords if any(v in k for v in ['impact', 'mission', 'purpose', 'culture', 'team'])]
        return values_terms[:3] if values_terms else keywords[:3]

    def _extract_lifestyle_terms(self, keywords: List[str], content: str) -> List[str]:
        """Extract lifestyle-focused search terms."""
        lifestyle_terms = [k for k in keywords if any(l in k for l in ['remote', 'flexible', 'balance', 'location', 'travel'])]
        return lifestyle_terms[:3] if lifestyle_terms else keywords[:3]

    def _extract_compensation_terms(self, keywords: List[str], content: str) -> List[str]:
        """Extract compensation-focused search terms."""
        comp_terms = [k for k in keywords if any(c in k for c in ['salary', 'equity', 'benefit', 'compens', 'senior', 'principal'])]
        return comp_terms[:3] if comp_terms else keywords[:3]


# Global instance for easy access
brand_search_helper = BrandSearchHelper()
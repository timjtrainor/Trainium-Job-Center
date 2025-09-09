"""
Retrieval and preprocessing components for job posting fit review.

This module provides YAML-first retrieval layer that prepares inputs for CrewAI tasks.
Functions normalize job descriptions using safe HTML cleaning and query ChromaDB 
for career brand insights. Designed to be lightweight, testable, and compatible
with YAML-defined crew workflows.
"""
import re
from typing import Dict, Any, Optional, List
from loguru import logger

# Safe HTML cleaning - prefer parser-based approaches over regex
# Bleach: Well-documented HTML sanitizer for security
# selectolax: Fast HTML parser, good for stripping tags efficiently  
import bleach
from selectolax.parser import HTMLParser

from ...models.job_posting import JobPosting
from ..infrastructure.chroma import get_chroma_client
from ..embeddings import get_embedding_function


def normalize_jd(text: str) -> str:
    """
    Normalize raw job description text for LLM consumption.
    
    Safely removes HTML, collapses whitespace, and deduplicates repeated bullets
    while preserving content structure. Uses parser-based HTML cleaning for safety.
    
    Args:
        text: Raw job description text (may contain HTML)
        
    Returns:
        Clean, normalized text suitable for LLM prompts
        
    References:
        - Bleach HTML sanitizer: https://bleach.readthedocs.io/
        - selectolax parser: https://selectolax.readthedocs.io/
    """
    if not text or not text.strip():
        return ""
        
    original_length = len(text)
    logger.debug(f"Normalizing JD text: {original_length} chars")
    
    # Step 1: Remove HTML safely using selectolax parser (faster than BeautifulSoup)
    # This is more reliable than regex for HTML parsing
    parser = HTMLParser(text)
    clean_text = parser.text()
    
    # Step 2: Also sanitize with bleach to ensure no residual HTML
    # Bleach is security-focused and handles edge cases well
    clean_text = bleach.clean(clean_text, tags=[], strip=True)
    
    # Step 3: Split into sentences/bullet points for deduplication
    # Split by common separators that indicate bullet points or distinct lines
    lines = re.split(r'[\n\r]+', clean_text)
    
    # Step 4: Clean and deduplicate each line
    seen_lines = set()
    deduplicated_lines = []
    
    for line in lines:
        # Clean the line
        line = line.strip()
        # Remove bullet markers and normalize
        line = re.sub(r'^[-*•\s]+', '', line).strip()
        
        if line and line not in seen_lines:
            seen_lines.add(line)
            deduplicated_lines.append(line)
    
    # Step 5: Rejoin and normalize spacing
    normalized_text = '\n'.join(deduplicated_lines)
    
    # Final cleanup - normalize whitespace within lines and between lines
    normalized_text = re.sub(r'[ \t]+', ' ', normalized_text)  # Single spaces only
    normalized_text = re.sub(r'\n\s*\n', '\n\n', normalized_text)  # Max 2 newlines
    normalized_text = normalized_text.strip()
    
    final_length = len(normalized_text)
    logger.debug(f"JD normalized: {original_length} -> {final_length} chars")
    
    return normalized_text


def get_career_brand_digest(profile_id: Optional[str] = None, k: int = 8, threshold: float = 0.2) -> Dict[str, Any]:
    """
    Query ChromaDB 'career_brand' collection for relevant career insights.
    
    Connects to Chroma, queries the career_brand collection, and returns a 
    token-budgeted digest string with metadata. Gracefully handles empty/unavailable
    collections.
    
    Args:
        profile_id: User profile ID for personalized queries (optional)
        k: Number of top similar documents to retrieve
        threshold: Minimum similarity score threshold for filtering
        
    Returns:
        Dict with digest string, doc_ids, scores, and metadata
        
    References:
        - ChromaDB docs: https://docs.trychroma.com/
        - Collection query API: https://docs.trychroma.com/usage-guide#querying-a-collection
    """
    logger.debug(f"Querying career_brand collection: profile_id={profile_id}, k={k}, threshold={threshold}")
    
    try:
        # Connect to ChromaDB using project's configured client
        client = get_chroma_client()
        embedding_function = get_embedding_function()
        
        # Try to get the career_brand collection
        try:
            collection = client.get_collection(
                name="career_brand",
                embedding_function=embedding_function
            )
        except Exception as e:
            logger.warning(f"Career brand collection not found or inaccessible: {e}")
            return {
                "digest": "",
                "doc_ids": [],
                "scores": [],
                "metadata": {
                    "error": "Collection unavailable",
                    "signal": "insufficient"
                }
            }
        
        # Check if collection has any documents
        doc_count = collection.count()
        if doc_count == 0:
            logger.info("Career brand collection is empty")
            return {
                "digest": "",
                "doc_ids": [],
                "scores": [],
                "metadata": {
                    "doc_count": 0,
                    "signal": "insufficient"
                }
            }
        
        # Build query text based on profile_id or use generic career query
        if profile_id:
            query_text = f"career development opportunities growth path advancement profile {profile_id}"
        else:
            query_text = "career development growth opportunities professional advancement"
        
        # Query collection using Chroma's documented flow
        # See: https://docs.trychroma.com/usage-guide#querying-a-collection
        results = collection.query(
            query_texts=[query_text],
            n_results=min(k, doc_count),  # Don't request more than available
            include=["documents", "metadatas", "distances"]
        )
        
        if not results["documents"] or not results["documents"][0]:
            logger.info("No matching documents found in career_brand collection")
            return {
                "digest": "",
                "doc_ids": [],
                "scores": [],
                "metadata": {
                    "doc_count": doc_count,
                    "signal": "insufficient"
                }
            }
        
        # Extract and filter results by threshold
        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []
        
        # Convert distances to similarity scores (Chroma uses cosine distance)
        similarities = [1.0 - d for d in distances] if distances else [1.0] * len(documents)
        
        # Filter by threshold
        filtered_docs = []
        filtered_ids = []
        filtered_scores = []
        
        for i, (doc, score) in enumerate(zip(documents, similarities)):
            if score >= threshold:
                filtered_docs.append(doc)
                filtered_scores.append(score)
                # Extract doc_id from metadata or generate from index
                if metadatas and len(metadatas) > i and metadatas[i]:
                    doc_id = metadatas[i].get('doc_id', f'doc_{i}')
                else:
                    doc_id = f'doc_{i}'
                filtered_ids.append(doc_id)
        
        # Build digest with ~2000 token budget (roughly 8000 chars)
        MAX_DIGEST_CHARS = 2000
        digest_parts = []
        current_length = 0
        
        for doc in filtered_docs:
            # Add separator between chunks
            separator = " | "
            doc_snippet = doc[:200] + "..." if len(doc) > 200 else doc
            
            if current_length + len(separator) + len(doc_snippet) > MAX_DIGEST_CHARS:
                break
                
            if digest_parts:  # Add separator before non-first items
                digest_parts.append(separator)
                current_length += len(separator)
                
            digest_parts.append(doc_snippet)
            current_length += len(doc_snippet)
        
        digest = "".join(digest_parts)
        
        logger.info(f"Career brand digest built: {len(filtered_docs)} chunks, {len(digest)} chars")
        
        return {
            "digest": digest,
            "doc_ids": filtered_ids,
            "scores": filtered_scores,
            "metadata": {
                "doc_count": doc_count,
                "retrieved": len(documents),
                "filtered": len(filtered_docs),
                "threshold": threshold,
                "signal": "sufficient" if filtered_docs else "insufficient"
            }
        }
        
    except Exception as e:
        logger.error(f"Error querying career_brand collection: {e}")
        return {
            "digest": "",
            "doc_ids": [],
            "scores": [],
            "metadata": {
                "error": str(e),
                "signal": "insufficient"
            }
        }


def build_context(job_posting: Dict[str, Any], profile_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Orchestrate normalization and retrieval to build complete context for YAML crew.
    
    Combines normalize_jd and get_career_brand_digest to prepare all inputs needed
    by the YAML-defined CrewAI tasks. Returns structured data with keys that align
    with YAML placeholder expectations.
    
    Args:
        job_posting: Dict with job posting data (title, company, description, etc.)
        profile_id: Optional user profile ID for personalized insights
        
    Returns:
        Dict with normalized_jd, career_brand_digest, doc_ids, scores, tags
        
    References:
        - CrewAI YAML docs: https://docs.crewai.com/how-to/Creating-a-Crew-and-kick-it-off/
        - YAML task variables: Support {job_description}, {career_brand_digest}, {job_meta}
    """
    logger.debug(f"Building context for job: {job_posting.get('title', 'Unknown')}")
    
    # Normalize job description text
    raw_description = job_posting.get('description', '')
    normalized_jd = normalize_jd(raw_description)
    
    # Get career brand insights
    career_data = get_career_brand_digest(profile_id=profile_id)
    
    # Extract basic tags using simple heuristics - keep deterministic and light
    tags = _extract_tags(job_posting)
    
    # Build the context that crew.py will forward to YAML placeholders
    context = {
        "normalized_jd": normalized_jd,
        "career_brand_digest": career_data["digest"],
        "doc_ids": career_data["doc_ids"],
        "scores": career_data["scores"],
        "tags": tags,
        # Additional metadata for debugging/monitoring
        "metadata": {
            "original_jd_length": len(raw_description),
            "normalized_jd_length": len(normalized_jd),
            "career_signal": career_data["metadata"].get("signal", "unknown"),
            "career_docs_retrieved": career_data["metadata"].get("retrieved", 0)
        }
    }
    
    logger.info(f"Context built successfully: {len(tags)} tags, {len(career_data['doc_ids'])} career docs")
    return context


def _extract_tags(job_posting: Dict[str, Any]) -> List[str]:
    """
    Extract minimal domain/seniority tags using simple heuristics.
    
    Deterministic tag extraction from title and description for categorization.
    Keeps logic simple and maintainable.
    
    Args:
        job_posting: Job posting data dict
        
    Returns:
        List of extracted tags
    """
    tags = set()
    
    title = job_posting.get('title', '').lower()
    description = job_posting.get('description', '').lower()
    combined_text = f"{title} {description}"
    
    # Domain tags
    domain_keywords = {
        'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning'],
        'data': ['data science', 'data analyst', 'analytics', 'big data', 'data engineer'],
        'platform': ['platform', 'infrastructure', 'devops', 'cloud', 'kubernetes'],
        'frontend': ['frontend', 'front-end', 'react', 'vue', 'angular', 'javascript'],
        'backend': ['backend', 'back-end', 'api', 'microservices', 'python', 'java'],
        'mobile': ['mobile', 'ios', 'android', 'react native', 'flutter'],
        'security': ['security', 'cybersecurity', 'infosec', 'compliance']
    }
    
    for tag, keywords in domain_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            tags.add(tag)
    
    # Seniority tags  
    seniority_keywords = {
        'entry': ['entry', 'junior', 'associate', 'graduate'],
        'mid': ['mid-level', 'intermediate', 'regular'],
        'senior': ['senior', 'sr.', 'sr ', 'experienced'],
        'staff': ['staff', 'principal', 'lead', 'architect'],
        'executive': ['director', 'vp', 'chief', 'head of', 'manager']
    }
    
    for tag, keywords in seniority_keywords.items():
        if any(keyword in title for keyword in keywords):
            tags.add(tag)
            break  # Only take highest seniority match
    
    return sorted(list(tags))  # Sort for deterministic output
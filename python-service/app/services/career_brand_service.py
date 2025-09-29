"""Career brand service for managing versioned career brand documents."""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from loguru import logger

from .chroma_manager import get_chroma_manager
from ..schemas.career_brand import (
    CareerBrandUploadRequest,
    CareerBrandUploadResponse,
    CareerBrandDocumentInfo,
    CareerBrandVersionHistory
)


class CareerBrandService:
    """Service for managing career brand documents with versioning."""

    def __init__(self):
        self.chroma_manager = get_chroma_manager()

    async def initialize(self):
        """Initialize the service and ChromaDB manager."""
        await self.chroma_manager.initialize()

    async def upload_career_brand_document(
        self,
        request: CareerBrandUploadRequest
    ) -> CareerBrandUploadResponse:
        """
        Upload a career brand document with automatic versioning.

        This replaces any existing document for the same section/narrative combo,
        ensuring only one latest version exists while preserving version history.
        """
        try:
            # Validate section value (should map to CrewAI agent section names)
            valid_sections = [
                "north_star_vision", "trajectory_mastery", "values_compass",
                "lifestyle_alignment", "compensation_philosophy", "purpose_impact",
                "industry_focus", "company_filters", "constraints"
            ]

            if request.section.lower() not in valid_sections:
                # Try to map user-friendly names to system names
                section_mapping = {
                    "north star": "north_star_vision",
                    "trajectory": "trajectory_mastery",
                    "values": "values_compass",
                    "values compass": "values_compass",
                    "positioning statement": "values_compass",  # Could be split later
                    "impact story": "values_compass",          # Could be split later
                    "signature capability": "trajectory_mastery",
                    "purpose": "purpose_impact",
                    "purpose and impact": "purpose_impact",
                    "purpose & impact": "purpose_impact",
                    "impact": "purpose_impact",
                    "industry": "industry_focus",
                    "industry focus": "industry_focus",
                    "company": "company_filters",
                    "company filters": "company_filters",
                    "constraints": "constraints",
                    "constraint": "constraints",
                    "deal-breakers": "constraints",
                    "deal breakers": "constraints"
                }

                mapped_section = section_mapping.get(request.section.lower())
                if mapped_section:
                    original_section = request.section
                    request.section = mapped_section
                    logger.info(f"Mapped user section '{original_section}' to '{mapped_section}'")
                else:
                    logger.warning(f"Unrecognized section: {request.section}")

            # Upload with versioning via ChromaManager
            result = await self.chroma_manager.upload_career_brand_document(
                section=request.section,
                content=request.content,
                title=request.title,
                narrative_id=request.profile_id  # narrative_id in our system
            )

            if result.success:
                # Get version info for response
                version_info = await self.chroma_manager.find_latest_by_section_and_narrative(
                    request.section, request.profile_id
                )

                version_number = version_info.get("version", 1) if version_info else 1

                logger.info(
                    f"Successfully uploaded career brand document: {request.section} "
                    f"v{version_number} for narrative {request.profile_id}"
                )

                return CareerBrandUploadResponse(
                    success=True,
                    message=f"Successfully uploaded {request.section} document v{version_number}",
                    document_id=result.document_id,
                    section=request.section,
                    version=version_number,
                    latest_version=True,
                    narrative_id=request.profile_id,
                    uploaded_at=datetime.now(timezone.utc).isoformat()
                )
            else:
                logger.error(f"Failed to upload career brand document: {result.message}")

                return CareerBrandUploadResponse(
                    success=False,
                    message=result.message,
                    document_id="",
                    section=request.section,
                    version=0,
                    latest_version=False,
                    narrative_id=request.profile_id
                )

        except Exception as e:
            error_msg = f"Failed to upload career brand document: {str(e)}"
            logger.error(error_msg)

            return CareerBrandUploadResponse(
                success=False,
                message=error_msg,
                document_id="",
                section=request.section if hasattr(request, 'section') else "unknown",
                version=0,
                latest_version=False,
                narrative_id=request.profile_id if hasattr(request, 'profile_id') else "unknown"
            )

    async def get_career_brand_documents(
        self,
        narrative_id: str,
        show_history: bool = False
    ) -> List[CareerBrandDocumentInfo]:
        """
        Get career brand documents for a narrative.

        Returns latest versions by default, or full history if show_history=True.
        """
        try:
            documents = []

            # Get all sections (complete 9-section career brand)
            sections = [
                "north_star_vision", "trajectory_mastery", "values_compass",
                "lifestyle_alignment", "compensation_philosophy", "purpose_impact",
                "industry_focus", "company_filters", "constraints"
            ]

            for section in sections:
                if show_history:
                    # Get full version history
                    versions = await self.chroma_manager.get_career_brand_version_history(
                        section, narrative_id, include_content=False
                    )

                    for version_info in versions:
                        documents.append(CareerBrandDocumentInfo(
                            id=version_info["document_id"],
                            title=version_info["title"] or f"Career Brand - {section.replace('_', ' ').title()}",
                            section=section,
                            latest_version=version_info["latest_version"],
                            version=version_info["version"],
                            created_at=version_info["uploaded_at"] or version_info["timestamp"],
                            content_preview=version_info["content_preview"],
                            narrative_id=narrative_id
                        ))
                else:
                    # Get only latest version
                    latest_doc = await self.chroma_manager.find_latest_by_section_and_narrative(
                        section, narrative_id
                    )

                    if latest_doc:
                        documents.append(CareerBrandDocumentInfo(
                            id=latest_doc["document_id"],
                            title=latest_doc["metadata"].get("title", f"Career Brand - {section.replace('_', ' ').title()}"),
                            section=section,
                            latest_version=True,
                            version=latest_doc["version"],
                            created_at=latest_doc["metadata"].get("uploaded_at") or latest_doc["metadata"].get("timestamp"),
                            content_preview=latest_doc["content"][:200] + "..." if len(latest_doc["content"]) > 200 else latest_doc["content"],
                            narrative_id=narrative_id
                        ))

            # Sort by creation date (newest first)
            documents.sort(key=lambda x: x.created_at, reverse=True)

            return documents

        except Exception as e:
            logger.error(f"Failed to get career brand documents for narrative {narrative_id}: {e}")
            return []

    async def delete_career_brand_document(
        self,
        document_id: str,
        narrative_id: str
    ) -> bool:
        """
        Delete a career brand document.

        Note: This permanently removes the document. For versioning, prefer to use the latest_version flag.
        """
        try:
            # Verify the document belongs to the narrative before deleting
            # (This would require a query to check ownership)

            logger.warning(
                f"Deleting career brand document {document_id} for narrative {narrative_id}. "
                "Consider marking as not latest instead of permanent deletion."
            )

            # For now, we'll allow deletion but this should be carefully managed
            # in production to maintain data integrity

            # Note: ChromaDB deletion would need to be implemented in ChromaManager
            # This is a placeholder for the deletion logic

            return False  # Placeholder - implement actual deletion logic

        except Exception as e:
            logger.error(f"Failed to delete career brand document {document_id}: {e}")
            return False


# Global service instance
_career_brand_service: Optional[CareerBrandService] = None


def get_career_brand_service() -> CareerBrandService:
    """Get the global career brand service instance."""
    global _career_brand_service
    if _career_brand_service is None:
        _career_brand_service = CareerBrandService()
    return _career_brand_service

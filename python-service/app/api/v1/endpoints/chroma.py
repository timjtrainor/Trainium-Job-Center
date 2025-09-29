"""ChromaDB management endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from loguru import logger
import json

from ....schemas.chroma import (
    ChromaUploadRequest,
    ChromaUploadResponse,
    ChromaCollectionListResponse,
    ChromaCollectionInfo
)
from ....services.chroma_service import ChromaService
from ....schemas.responses import create_success_response, create_error_response


router = APIRouter()


def get_chroma_service() -> ChromaService:
    """Dependency to get ChromaService instance."""
    return ChromaService()


@router.post("/documents/career-brand/full")
async def upload_full_career_brand_document(
    file: UploadFile = File(..., description="Full career brand document in Markdown format"),
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """Upload a full career brand document and automatically split by H1 headers."""
    from typing import List, Dict, Any
    import re
    from datetime import datetime, timezone

    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.txt', '.md', '.markdown')):
            raise HTTPException(
                status_code=400,
                detail="Only text/markdown files (.txt, .md, .markdown) are supported"
            )

        # Read file content
        try:
            content = await file.read()
            document_text = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File must be valid UTF-8 encoded text"
            )

        if not document_text.strip():
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty"
            )

        # Parse H1 headers and split document
        def parse_h1_sections(markdown_content: str) -> List[Dict[str, Any]]:
            """Parse markdown content into sections based on H1 headers."""
            # Split by H1 headers but not H2 headers
            # Match lines that start with # followed by space (not ##)
            h1_pattern = r'(?=^# [^\n]+$)'  # Positive lookahead for H1 headers
            sections = re.split(h1_pattern, markdown_content, flags=re.MULTILINE)

            parsed_sections = []
            current_title = ""
            current_content = []

            for section in sections:
                if not section.strip():
                    continue

                lines = section.strip().split('\n')
                if lines and lines[0].startswith('# '):
                    # Found H1 header
                    if current_title and current_content:
                        # Save previous section
                        section_content = '\n'.join(current_content).strip()
                        if section_content:
                            parsed_sections.append({
                                "title": current_title,
                                "content": section_content
                            })

                    # Start new section
                    current_title = lines[0][2:].strip()  # Remove '# ' prefix
                    current_content = lines[1:] if len(lines) > 1 else []  # Skip header line
                else:
                    # Continuation of current section
                    current_content.extend(lines)

            # Add final section
            if current_title and current_content:
                section_content = '\n'.join(current_content).strip()
                if section_content:
                    parsed_sections.append({
                        "title": current_title,
                        "content": section_content
                    })

            return parsed_sections

        def map_section_to_career_brand_category(title: str) -> str:
            """Map section titles to Career Brand categories."""
            title_lower = title.lower()

            # Direct mappings
            if 'north star' in title_lower:
                return 'North Star'
            elif 'trajectory' in title_lower or 'mastery' in title_lower:
                return 'Trajectory & Mastery'
            elif 'values' in title_lower:
                return 'Values'
            elif 'positioning' in title_lower:
                return 'Positioning Statement'
            elif 'signature' in title_lower:
                return 'Signature Capability'
            elif 'impact' in title_lower:
                return 'Impact Story'
            elif 'lifestyle' in title_lower:
                return 'Lifestyle Alignment'
            elif 'compensation' in title_lower:
                return 'Compensation Philosophy'
            elif 'purpose' in title_lower:
                return 'Purpose & Impact'
            elif 'industry' in title_lower:
                return 'Industry Focus'
            elif 'company' in title_lower and 'filter' in title_lower:
                return 'Company Filters'
            elif 'constraint' in title_lower:
                return 'Constraints'
            elif 'narrative' in title_lower or 'proof' in title_lower:
                return 'Narratives & Proof Points'
            elif 'career story' in title_lower:
                return 'Career Story'

            # Default fallback
            return title.strip()

        # Parse the document
        sections = parse_h1_sections(document_text)

        if not sections:
            raise HTTPException(
                status_code=400,
                detail="No H1 sections found in the document. Ensure main sections start with '# ' (not '## ')"
            )

        # Initialize service
        await chroma_service.initialize()

        uploaded_sections = []

        for section in sections:
            try:
                # Skip metadata/version sections (typically start with Version/Updated)
                if any(keyword in section["title"].lower() for keyword in ['version', 'updated', 'last updated', 'review cadence']):
                    continue

                # Map to career brand category
                career_brand_category = map_section_to_career_brand_category(section["title"])

                # Generate unique collection name
                collection_name = f"career_brand_{chroma_service._sha1_hash(career_brand_category)[:8]}"

                # Create metadata
                uploaded_at = datetime.now(timezone.utc).isoformat()
                metadata = {
                    "profile_id": "",  # Will be set from query param or extracted
                    "section": career_brand_category,
                    "source": file.filename or "uploaded_document",
                    "original_title": section["title"],
                    "uploaded_at": uploaded_at
                }

                # Create upload request
                request = ChromaUploadRequest(
                    collection_name=collection_name,
                    title=f"{career_brand_category} - {section['title']}",
                    tags=["career_brand", "full_document_upload"],
                    document_text=section["content"],
                    metadata=metadata
                )

                # Upload to ChromaDB
                result = await chroma_service.upload_document(request)

                if result.success:
                    uploaded_sections.append({
                        "original_title": section["title"],
                        "career_brand_category": career_brand_category,
                        "collection_name": collection_name,
                        "chunks_created": result.chunks_created,
                        "document_id": result.document_id
                    })
                else:
                    # Log error but continue with other sections
                    logger.error(f"Failed to upload section '{section['title']}': {result.message}")

            except Exception as e:
                logger.error(f"Error processing section '{section['title']}': {e}")
                continue

        if not uploaded_sections:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload any sections. Check document format and try again."
            )

        return {
            "message": f"Successfully uploaded {len(uploaded_sections)} career brand sections",
            "sections_uploaded": uploaded_sections,
            "total_sections_found": len(sections)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in full career brand upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/chroma/upload", response_model=ChromaUploadResponse)
async def upload_to_chroma(
    collection_name: str = Form(..., description="Name of the ChromaDB collection"),
    title: str = Form(..., description="Title for the document"),
    tags: str = Form(default="", description="Comma-separated tags"),
    file: UploadFile = File(..., description="Text file to upload"),
    metadata: str = Form(default="{}", description="JSON string of additional metadata"),
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """
    Upload a text file to ChromaDB with user-defined metadata.

    - **collection_name**: Name for the ChromaDB collection
    - **title**: Title for the document
    - **tags**: Comma-separated list of tags
    - **file**: Text file to upload (.txt, .md, etc.)
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.txt', '.md', '.text')):
            raise HTTPException(
                status_code=400,
                detail="Only text files (.txt, .md, .text) are supported"
            )

        # Read file content
        try:
            content = await file.read()
            document_text = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File must be valid UTF-8 encoded text"
            )

        if not document_text.strip():
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty"
            )

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []

        # Parse metadata
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
            if not isinstance(metadata_dict, dict):
                raise ValueError("Metadata must be a JSON object")
        except (json.JSONDecodeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Metadata must be a valid JSON object",
            )

        # Create request object
        request = ChromaUploadRequest(
            collection_name=collection_name,
            title=title,
            tags=tag_list,
            document_text=document_text,
            metadata=metadata_dict,
        )

        # Initialize service if needed
        await chroma_service.initialize()

        # Upload to ChromaDB
        result = await chroma_service.upload_document(request)

        if result.success:
            logger.info(
                f"Successfully uploaded file '{file.filename}' to collection '{collection_name}'"
            )
        else:
            # Log the detailed error for debugging
            logger.error(
                f"Failed to upload file '{file.filename}' to collection '{collection_name}': "
                f"{result.message}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chroma upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/chroma/upload-text", response_model=ChromaUploadResponse)
async def upload_text_to_chroma(
    request: ChromaUploadRequest,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """
    Upload text directly to ChromaDB with user-defined metadata.

    Alternative endpoint for uploading text content without file upload.
    """
    try:
        if not request.document_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Document text cannot be empty"
            )

        # Initialize service if needed
        await chroma_service.initialize()

        # Upload to ChromaDB
        result = await chroma_service.upload_document(request)

        if result.success:
            logger.info(
                f"Successfully uploaded text to collection '{request.collection_name}'"
            )
        else:
            # Log the detailed error for debugging
            logger.error(
                f"Failed to upload text to collection '{request.collection_name}': "
                f"{result.message}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chroma text upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/chroma/collections", response_model=ChromaCollectionListResponse)
async def list_chroma_collections(
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """List all ChromaDB collections with their metadata."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()

        collections = await chroma_service.list_collections()

        return ChromaCollectionListResponse(collections=collections)

    except Exception as e:
        logger.error(f"Failed to list ChromaDB collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.delete("/chroma/collections/{collection_name}")
async def delete_chroma_collection(
    collection_name: str,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """Delete a ChromaDB collection."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()

        success = await chroma_service.delete_collection(collection_name)

        if success:
            return create_success_response(
                message=f"Successfully deleted collection '{collection_name}'"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to delete collection '{collection_name}'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collection '{collection_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete collection: {str(e)}"
        )


@router.get("/chroma/collections/{collection_name}/documents")
async def list_collection_documents(
    collection_name: str,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """List all documents in a ChromaDB collection."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()

        documents = await chroma_service.list_documents(collection_name)

        return {"documents": documents}

    except Exception as e:
        logger.error(f"Failed to list documents in collection '{collection_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/documents")
async def get_documents(
    profile_id: str,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """Get all documents for a specific profile ID across all document collections."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()

        # List of document collections to query
        document_collections = [
            "career_brand",
            "career_paths",
            "job_search_strategies",
            "resumes"
        ]

        client = chroma_service._get_client()
        all_documents = []

        # Query each document collection
        for collection_name in document_collections:
            try:
                # Check if collection exists
                try:
                    collection = client.get_collection(collection_name)
                except Exception:
                    # Collection doesn't exist, skip
                    continue

                # Get all documents with metadata
                result = collection.get(include=["metadatas"])

                if result["ids"] and result["metadatas"]:
                    for i, chunk_id in enumerate(result["ids"]):
                        metadata = result["metadatas"][i]

                        # Only include documents that match the profile_id
                        doc_profile_id = metadata.get("profile_id")
                        if doc_profile_id != profile_id:
                            continue

                        # Determine the logical document id (shared across chunks)
                        document_id = metadata.get(
                            "doc_id",
                            chunk_id.split("::")[0] if "::" in chunk_id else chunk_id
                        )

                        # Create document object in expected format
                        document = {
                            "id": document_id,
                            "title": metadata.get("title", "Untitled"),
                            "content": "",  # Frontend doesn't need full content
                            "content_type": collection_name,
                            "section": metadata.get("section", ""),
                            "created_at": metadata.get("created_at", ""),
                            "metadata": metadata
                        }

                        # Avoid duplicates
                        if not any(doc["id"] == document_id for doc in all_documents):
                            all_documents.append(document)

            except Exception as e:
                logger.warning(f"Failed to query collection {collection_name}: {e}")
                continue

        return {"documents": all_documents}

    except Exception as e:
        logger.error(f"Failed to get documents for profile {profile_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get documents: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document_by_id(
    document_id: str,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """Delete a document by its ID across all collections."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()

        # List of document collections to search
        document_collections = [
            "career_brand",
            "career_paths",
            "job_search_strategies",
            "resumes"
        ]

        client = chroma_service._get_client()
        deleted = False

        # Search each collection for the document
        for collection_name in document_collections:
            try:
                # Check if collection exists
                try:
                    collection = client.get_collection(collection_name)
                except Exception:
                    # Collection doesn't exist, skip
                    continue

                # Get all documents to find matching document_id
                result = collection.get(include=["metadatas"])

                if result["ids"] and result["metadatas"]:
                    for i, chunk_id in enumerate(result["ids"]):
                        metadata = result["metadatas"][i]

                        # Check if this document matches the target ID
                        doc_id = metadata.get(
                            "doc_id",
                            chunk_id.split("::")[0] if "::" in chunk_id else chunk_id
                        )

                        if doc_id == document_id:
                            # Delete this document using the service method
                            success = await chroma_service.delete_document(collection_name, document_id)
                            if success:
                                deleted = True
                                logger.info(f"Successfully deleted document {document_id} from collection {collection_name}")
                                break  # Document found and deleted, exit inner loop

                    if deleted:
                        break  # Document deleted, exit outer loop

            except Exception as e:
                logger.warning(f"Error checking collection {collection_name}: {e}")
                continue

        if deleted:
            return {"message": f"Successfully deleted document {document_id}"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.delete("/chroma/collections/{collection_name}/documents/{document_id}")
async def delete_collection_document(
    collection_name: str,
    document_id: str,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """Delete a specific document from a ChromaDB collection."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()

        success = await chroma_service.delete_document(collection_name, document_id)

        if success:
            return create_success_response(
                message=f"Successfully deleted document '{document_id}' from collection '{collection_name}'"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' not found in collection '{collection_name}'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document '{document_id}' from collection '{collection_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

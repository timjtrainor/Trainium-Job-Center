# ChromaDB Document Upload Feature

This feature allows users to upload text documents to ChromaDB through a web interface, replacing the need to modify hardcoded Python scripts.

## What Changed

### Before
- Users had to modify `chroma_data_loader.py` directly
- Collection name, title, tags, and document text were hardcoded
- Required Python knowledge to change document content

### After
- Web-based upload interface accessible from the main navigation
- User-configurable collection name, title, and tags
- File upload support for .txt, .md, and .text files
- Collection management (view and delete collections)
- No code changes required

## Features

### Backend (Python FastAPI)
- **New API Endpoints:**
  - `POST /chroma/upload` - Upload files with metadata
  - `POST /chroma/upload-text` - Upload text directly
  - `GET /chroma/collections` - List all collections
  - `DELETE /chroma/collections/{name}` - Delete a collection

- **New Services:**
  - `ChromaService` - Manages ChromaDB operations
  - Automatic text chunking (300 words with 50-word overlap)
  - Uses BAAI/bge-m3 embedding model
  - Supports both HTTP and persistent ChromaDB clients

### Frontend (React/TypeScript)
- **New Component:** `ChromaUploadView`
- File drag-and-drop interface
- Form validation and error handling
- Collection management interface
- Upload progress and status feedback

### Infrastructure
- **ChromaDB Container:** Added to docker-compose.yml
- **Fallback Support:** Uses persistent client if HTTP server unavailable
- **Environment Variables:** Configurable ChromaDB connection

## Usage

1. **Navigate to ChromaDB Upload:** Click "ChromaDB Upload" in the sidebar
2. **Fill the Form:**
   - Collection Name: Choose a name (will be created if doesn't exist)
   - Title: Descriptive title for your document
   - Tags: Comma-separated tags (optional)
3. **Upload File:** Select a .txt, .md, or .text file
4. **Submit:** Click "Upload Document"

## Testing

Use the provided `sample-document.txt` file to test the upload functionality.

## Docker Setup

The system now includes ChromaDB as a service:
- **ChromaDB UI:** http://localhost:8001 (when running docker-compose)
- **API:** Available at http://localhost:8000/docs for API documentation

## Example Code

See `python-service/app/services/tools/chroma_upload_example.py` for programmatic usage of the new service.

## Files Modified/Added

### Backend
- `python-service/app/schemas/chroma.py` - Request/response schemas
- `python-service/app/services/chroma_service.py` - ChromaDB service layer
- `python-service/app/api/v1/endpoints/chroma.py` - API endpoints
- `python-service/app/api/router.py` - Added chroma router
- `python-service/app/services/infrastructure/chroma.py` - Enhanced client with fallback

### Frontend
- `components/ChromaUploadView.tsx` - Upload interface
- `components/IconComponents.tsx` - Added CircleStackIcon
- `components/SideNav.tsx` - Added navigation link
- `App.tsx` - Added route

### Infrastructure
- `docker-compose.yml` - Added ChromaDB service
- `.env.example` - Updated ChromaDB configuration

### Examples/Documentation
- `sample-document.txt` - Test document
- `python-service/app/services/tools/chroma_upload_example.py` - Usage example
import React, { useState, useRef } from 'react';
import { CloudArrowUpIcon, DocumentTextIcon, TrashIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

interface ChromaUploadProps {
    onBack?: () => void;
}

interface CollectionInfo {
    name: string;
    count: number;
    metadata?: any;
}

interface UploadResponse {
    success: boolean;
    message: string;
    collection_name: string;
    document_id: string;
    chunks_created: number;
}

export const ChromaUploadView: React.FC<ChromaUploadProps> = ({ onBack }) => {
    const [collectionName, setCollectionName] = useState('');
    const [title, setTitle] = useState('');
    const [tags, setTags] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
    const [collections, setCollections] = useState<CollectionInfo[]>([]);
    const [isLoadingCollections, setIsLoadingCollections] = useState(false);
    const [showCollections, setShowCollections] = useState(false);
    
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validate file type
            const allowedTypes = ['.txt', '.md', '.text'];
            const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
            
            if (!allowedTypes.includes(fileExtension)) {
                alert('Please select a text file (.txt, .md, .text)');
                return;
            }
            
            setSelectedFile(file);
            
            // Auto-populate title if empty
            if (!title) {
                const nameWithoutExtension = file.name.substring(0, file.name.lastIndexOf('.'));
                setTitle(nameWithoutExtension);
            }
        }
    };

    const handleUpload = async () => {
        if (!collectionName.trim() || !title.trim() || !selectedFile) {
            alert('Please fill in all required fields and select a file');
            return;
        }

        setIsUploading(true);
        setUploadResult(null);

        try {
            const formData = new FormData();
            formData.append('collection_name', collectionName.trim());
            formData.append('title', title.trim());
            formData.append('tags', tags.trim());
            formData.append('file', selectedFile);

            const response = await fetch('http://localhost:8000/chroma/upload', {
                method: 'POST',
                body: formData,
            });

            const result: UploadResponse = await response.json();
            
            if (response.ok) {
                setUploadResult(result);
                // Clear form on success
                setCollectionName('');
                setTitle('');
                setTags('');
                setSelectedFile(null);
                if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                }
            } else {
                setUploadResult({
                    success: false,
                    message: result.message || 'Upload failed',
                    collection_name: collectionName,
                    document_id: '',
                    chunks_created: 0
                });
            }
        } catch (error) {
            console.error('Upload error:', error);
            setUploadResult({
                success: false,
                message: `Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
                collection_name: collectionName,
                document_id: '',
                chunks_created: 0
            });
        } finally {
            setIsUploading(false);
        }
    };

    const loadCollections = async () => {
        setIsLoadingCollections(true);
        try {
            const response = await fetch('http://localhost:8000/chroma/collections');
            const result = await response.json();
            
            if (response.ok) {
                setCollections(result.collections || []);
            } else {
                console.error('Failed to load collections:', result);
                setCollections([]);
            }
        } catch (error) {
            console.error('Error loading collections:', error);
            setCollections([]);
        } finally {
            setIsLoadingCollections(false);
        }
    };

    const deleteCollection = async (collectionName: string) => {
        if (!confirm(`Are you sure you want to delete collection "${collectionName}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`http://localhost:8000/chroma/collections/${encodeURIComponent(collectionName)}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                // Reload collections after successful deletion
                await loadCollections();
            } else {
                const result = await response.json();
                alert(`Failed to delete collection: ${result.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Delete error:', error);
            alert(`Failed to delete collection: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    };

    const toggleCollections = async () => {
        if (!showCollections) {
            await loadCollections();
        }
        setShowCollections(!showCollections);
    };

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-200">
                        ChromaDB Document Upload
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-2">
                        Upload text documents to ChromaDB for vector search and AI assistance
                    </p>
                </div>
                {onBack && (
                    <button
                        onClick={onBack}
                        className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                    >
                        ← Back
                    </button>
                )}
            </div>

            {/* Upload Form */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200 mb-4">
                    Upload Document
                </h2>

                <div className="space-y-4">
                    {/* Collection Name */}
                    <div>
                        <label htmlFor="collection" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Collection Name *
                        </label>
                        <input
                            id="collection"
                            type="text"
                            value={collectionName}
                            onChange={(e) => setCollectionName(e.target.value)}
                            className="w-full p-3 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g., my-documents, knowledge-base"
                        />
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                            Collection will be created if it doesn't exist
                        </p>
                    </div>

                    {/* Title */}
                    <div>
                        <label htmlFor="title" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Document Title *
                        </label>
                        <input
                            id="title"
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full p-3 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g., Project Documentation, Meeting Notes"
                        />
                    </div>

                    {/* Tags */}
                    <div>
                        <label htmlFor="tags" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Tags (Optional)
                        </label>
                        <input
                            id="tags"
                            type="text"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            className="w-full p-3 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g., documentation, project, important"
                        />
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                            Separate multiple tags with commas
                        </p>
                    </div>

                    {/* File Upload */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                            Text File *
                        </label>
                        <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-6 text-center">
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".txt,.md,.text"
                                onChange={handleFileSelect}
                                className="hidden"
                                id="file-upload"
                            />
                            <label htmlFor="file-upload" className="cursor-pointer">
                                <CloudArrowUpIcon className="h-12 w-12 mx-auto text-slate-400 dark:text-slate-500 mb-3" />
                                <p className="text-sm text-slate-600 dark:text-slate-400">
                                    {selectedFile ? (
                                        <span className="font-medium text-blue-600 dark:text-blue-400">
                                            {selectedFile.name}
                                        </span>
                                    ) : (
                                        <>
                                            <span className="font-medium text-blue-600 dark:text-blue-400">Click to upload</span>
                                            <span> or drag and drop</span>
                                        </>
                                    )}
                                </p>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                    TXT, MD files up to 10MB
                                </p>
                            </label>
                        </div>
                    </div>

                    {/* Upload Button */}
                    <button
                        onClick={handleUpload}
                        disabled={isUploading || !collectionName.trim() || !title.trim() || !selectedFile}
                        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-md transition-colors"
                    >
                        {isUploading ? 'Uploading...' : 'Upload Document'}
                    </button>
                </div>

                {/* Upload Result */}
                {uploadResult && (
                    <div className={`mt-4 p-4 rounded-md ${
                        uploadResult.success 
                            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' 
                            : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                    }`}>
                        <div className="flex items-start">
                            <InformationCircleIcon className={`h-5 w-5 mt-0.5 mr-3 ${
                                uploadResult.success ? 'text-green-500' : 'text-red-500'
                            }`} />
                            <div>
                                <p className={`font-medium ${
                                    uploadResult.success ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'
                                }`}>
                                    {uploadResult.success ? 'Upload Successful!' : 'Upload Failed'}
                                </p>
                                <p className={`text-sm mt-1 ${
                                    uploadResult.success ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'
                                }`}>
                                    {uploadResult.message}
                                </p>
                                {uploadResult.success && (
                                    <div className="text-xs text-green-600 dark:text-green-400 mt-2">
                                        <p>Collection: {uploadResult.collection_name}</p>
                                        <p>Document ID: {uploadResult.document_id}</p>
                                        <p>Text chunks created: {uploadResult.chunks_created}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Collections Management */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">
                        Manage Collections
                    </h2>
                    <button
                        onClick={toggleCollections}
                        className="px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                    >
                        {showCollections ? 'Hide Collections' : 'Show Collections'}
                    </button>
                </div>

                {showCollections && (
                    <div>
                        {isLoadingCollections ? (
                            <p className="text-slate-600 dark:text-slate-400">Loading collections...</p>
                        ) : collections.length > 0 ? (
                            <div className="space-y-3">
                                {collections.map((collection) => (
                                    <div
                                        key={collection.name}
                                        className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-md"
                                    >
                                        <div className="flex items-center">
                                            <DocumentTextIcon className="h-5 w-5 text-slate-400 mr-3" />
                                            <div>
                                                <p className="font-medium text-slate-800 dark:text-slate-200">
                                                    {collection.name}
                                                </p>
                                                <p className="text-sm text-slate-600 dark:text-slate-400">
                                                    {collection.count} documents
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => deleteCollection(collection.name)}
                                            className="p-2 text-red-500 hover:text-red-700 dark:hover:text-red-400"
                                            title="Delete collection"
                                        >
                                            <TrashIcon className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-slate-600 dark:text-slate-400">No collections found</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
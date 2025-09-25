import React, { useState, useRef, useEffect, useMemo } from 'react';
import { DocumentTextIcon, TrashIcon, EyeIcon, SparklesIcon, ArrowUturnLeftIcon, CheckIcon, RocketLaunchIcon } from './IconComponents';
import * as apiService from '../services/apiService';
// FIX: Add UploadSuccessResponse to the import from types.
import { StrategicNarrative, UploadedDocument, ContentType, UploadSuccessResponse } from '../types';
import { useToast } from '../hooks/useToast';

interface ChromaUploadViewProps {
    strategicNarratives: StrategicNarrative[];
    activeNarrativeId: string | null;
}

const CONTENT_TYPES: { [key in ContentType]: { name: string; description: string; endpoint: string; sections: string[] } } = {
    career_brand: {
        name: 'Career Brand',
        description: 'Upload one of your 9 brand framework sections',
        endpoint: '/career-brand',
        sections: ['North Star', 'Values', 'Positioning Statement', 'Signature Capability', 'Impact Story'],
    },
    career_path: {
        name: 'Career Path',
        description: 'Upload a career trajectory or milestones document',
        endpoint: '/career-paths',
        sections: ['Milestones', 'Growth Themes', 'Skill Gaps', 'Target Roles'],
    },
    job_search_strategy: {
        name: 'Job Search Strategy',
        description: 'Upload a strategy or playbook document',
        endpoint: '/job-search-strategies',
        sections: ['Networking', 'Applications', 'Referrals', 'Interview Prep'],
    },
    resume: {
        name: 'Resume',
        description: 'Upload your latest resume as a text file',
        endpoint: '/resume',
        sections: ['resume'],
    },
};

const TypeSelectionStep = ({ onSelect }: { onSelect: (type: ContentType) => void }) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(CONTENT_TYPES).map(([key, { name, description }]) => (
            <button key={key} onClick={() => onSelect(key as ContentType)} className="text-left p-4 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                <h3 className="font-semibold text-slate-800 dark:text-slate-200">{name}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">{description}</p>
            </button>
        ))}
    </div>
);

const DocumentViewer = ({ strategicNarratives, activeNarrativeId }: { strategicNarratives: StrategicNarrative[], activeNarrativeId: string | null }) => {
    const [selectedNarrative, setSelectedNarrative] = useState(activeNarrativeId || '');
    const [documents, setDocuments] = useState<UploadedDocument[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showHistory, setShowHistory] = useState(false);

    useEffect(() => {
        if (selectedNarrative) {
            fetchDocuments();
        } else {
            setDocuments([]);
        }
    }, [selectedNarrative]);

    const fetchDocuments = async () => {
        setIsLoading(true);
        try {
            const docs = await apiService.getUploadedDocuments(selectedNarrative);
            setDocuments(docs);
        } catch (error) {
            console.error("Failed to fetch documents:", error);
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleDelete = async (docId: string) => {
        if (window.confirm("Are you sure you want to delete this document?")) {
            await apiService.deleteUploadedDocument(docId);
            fetchDocuments(); // Refresh list
        }
    };

    const displayedDocuments = useMemo(() => {
        if (showHistory) {
            return documents;
        }
        const latestDocs = new Map<string, UploadedDocument>();
        for (const doc of documents) {
            const key = `${doc.content_type}-${doc.section}`;
            const existing = latestDocs.get(key);
            if (!existing || new Date(doc.created_at) > new Date(existing.created_at)) {
                latestDocs.set(key, doc);
            }
        }
        return Array.from(latestDocs.values());
    }, [documents, showHistory]);

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <select value={selectedNarrative} onChange={e => setSelectedNarrative(e.target.value)} className="w-full max-w-xs p-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700">
                    <option value="">Select a Narrative...</option>
                    {strategicNarratives.map(n => <option key={n.narrative_id} value={n.narrative_id}>{n.narrative_name}</option>)}
                </select>
                <div className="flex items-center">
                    <span className="text-sm mr-2">Show History</span>
                    <input type="checkbox" checked={showHistory} onChange={e => setShowHistory(e.target.checked)} className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"/>
                </div>
            </div>
            {isLoading ? <p>Loading documents...</p> : (
                <div className="space-y-2">
                    {displayedDocuments.map(doc => (
                        <div key={doc.id} className="p-3 bg-slate-100 dark:bg-slate-700/50 rounded-md flex justify-between items-center">
                            <div>
                                <p className="font-semibold">{doc.title}</p>
                                <p className="text-xs text-slate-500 dark:text-slate-400">{doc.content_type} / {doc.section} / {new Date(doc.created_at).toLocaleString()}</p>
                            </div>
                            <button onClick={() => handleDelete(doc.id)} className="p-1 text-red-500 hover:text-red-400"><TrashIcon className="h-4 w-4"/></button>
                        </div>
                    ))}
                    {documents.length === 0 && selectedNarrative && <p className="text-center text-sm text-slate-500 py-4">No documents found for this narrative.</p>}
                </div>
            )}
        </div>
    );
};

export const ChromaUploadView = ({ strategicNarratives, activeNarrativeId }: ChromaUploadViewProps) => {
    const [step, setStep] = useState<'select' | 'details'>('select');
    const [contentType, setContentType] = useState<ContentType | null>(null);
    const [narrativeId, setNarrativeId] = useState(activeNarrativeId || '');
    const [section, setSection] = useState('');
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [errors, setErrors] = useState<{ [key: string]: string }>({});

    const fileInputRef = useRef<HTMLInputElement>(null);
    const { addToast } = useToast();

    useEffect(() => {
        if (activeNarrativeId) {
            setNarrativeId(activeNarrativeId);
        }
    }, [activeNarrativeId]);

    const handleTypeSelect = (type: ContentType) => {
        setContentType(type);
        setSection(CONTENT_TYPES[type].sections[0] || ''); // Default to first section
        setStep('details');
    };

    const handleBack = () => {
        setContentType(null);
        setStep('select');
        // Reset form fields
        setTitle('');
        setContent('');
        setFile(null);
        setErrors({});
    };

    const validate = () => {
        const newErrors: { [key: string]: string } = {};
        if (!narrativeId) newErrors.narrative = "Narrative is required.";
        if (!title.trim()) newErrors.title = "Title is required.";
        if (contentType !== 'resume' && !content.trim()) {
            newErrors.content = "Content is required.";
        }
        if (contentType === 'resume' && !file) {
            newErrors.file = "A file is required for resume uploads.";
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };
    
    const handleSubmit = async () => {
        if (!validate()) return;
        
        setIsUploading(true);
        try {
            let result: UploadSuccessResponse;
            const finalSection = contentType === 'resume' ? 'resume' : section;

            if (contentType === 'resume' && file) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('profile_id', narrativeId);
                formData.append('section', finalSection);
                formData.append('title', title);
                formData.append('metadata', JSON.stringify({ uploaded_at: new Date().toISOString() }));
                result = await apiService.uploadResume(formData);
            } else {
                const payload = {
                    profile_id: narrativeId,
                    section: finalSection,
                    title,
                    content,
                    metadata: { uploaded_at: new Date().toISOString() }
                };
                switch (contentType) {
                    case 'career_brand': result = await apiService.uploadCareerBrand(payload); break;
                    case 'career_path': result = await apiService.uploadCareerPath(payload); break;
                    case 'job_search_strategy': result = await apiService.uploadJobSearchStrategy(payload); break;
                    default: throw new Error("Invalid content type");
                }
            }
            addToast("Upload successful!", 'success');
            handleBack(); // Go back to selection screen
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Upload failed', 'error');
        } finally {
            setIsUploading(false);
        }
    };

    const inputClass = "w-full p-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700";
    const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1";

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Document Uploader</h1>
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                {step === 'select' ? (
                    <>
                        <h2 className="text-xl font-semibold mb-4">What are you uploading?</h2>
                        <TypeSelectionStep onSelect={handleTypeSelect} />
                    </>
                ) : contentType && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h2 className="text-xl font-semibold">Details for: <span className="text-blue-600 dark:text-blue-400">{CONTENT_TYPES[contentType].name}</span></h2>
                            <button onClick={handleBack} className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1">
                                <ArrowUturnLeftIcon className="h-4 w-4"/> Back
                            </button>
                        </div>

                        <div>
                            <label htmlFor="narrativeId" className={labelClass}>Narrative</label>
                            <select id="narrativeId" value={narrativeId} onChange={e => setNarrativeId(e.target.value)} className={inputClass}>
                                {strategicNarratives.map(n => <option key={n.narrative_id} value={n.narrative_id}>{n.narrative_name}</option>)}
                            </select>
                            {errors.narrative && <p className="text-xs text-red-500 mt-1">{errors.narrative}</p>}
                        </div>

                        {contentType !== 'resume' && (
                            <div>
                                <label htmlFor="section" className={labelClass}>Section</label>
                                <select id="section" value={section} onChange={e => setSection(e.target.value)} className={inputClass}>
                                    {CONTENT_TYPES[contentType].sections.map(s => <option key={s} value={s}>{s}</option>)}
                                </select>
                            </div>
                        )}
                        
                        <div>
                            <label htmlFor="title" className={labelClass}>Title</label>
                            <input type="text" id="title" value={title} onChange={e => setTitle(e.target.value)} className={inputClass} />
                            {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title}</p>}
                        </div>

                        {contentType === 'resume' ? (
                            <div>
                                <label htmlFor="file" className={labelClass}>Resume File</label>
                                <input type="file" id="file" ref={fileInputRef} onChange={e => setFile(e.target.files ? e.target.files[0] : null)} accept=".txt,.md" className="text-sm" />
                                <p className="text-xs text-slate-500 mt-1">Please upload a plain text (.txt, .md) file. PDF/DOCX support requires additional libraries.</p>
                                {errors.file && <p className="text-xs text-red-500 mt-1">{errors.file}</p>}
                            </div>
                        ) : (
                            <div>
                                <label htmlFor="content" className={labelClass}>Content</label>
                                <textarea id="content" value={content} onChange={e => setContent(e.target.value)} rows={8} className={inputClass}></textarea>
                                {errors.content && <p className="text-xs text-red-500 mt-1">{errors.content}</p>}
                            </div>
                        )}
                        
                        <button onClick={handleSubmit} disabled={isUploading} className="w-full py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:bg-blue-400">
                            {isUploading ? 'Uploading...' : 'Upload'}
                        </button>
                    </div>
                )}
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                 <h2 className="text-xl font-semibold mb-4">View Uploaded Documents</h2>
                 <DocumentViewer strategicNarratives={strategicNarratives} activeNarrativeId={activeNarrativeId}/>
            </div>
        </div>
    );
};
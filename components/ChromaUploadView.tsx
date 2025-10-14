import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { ArrowUturnLeftIcon, CheckIcon, RocketLaunchIcon, TrashIcon } from './IconComponents';
import * as apiService from '../services/apiService';
import { FASTAPI_BASE_URL } from '../constants';
import { StrategicNarrative, UploadedDocument, DocumentDetail } from '../types';
import { useToast } from '../hooks/useToast';

type NarrativeContentType = 'career_brand' | 'career_brand_full' | 'career_path' | 'job_search_strategy';

type TabKey = 'narratives' | 'proofPoints' | 'resumes';

const NARRATIVE_CONTENT_TYPES: Record<
    NarrativeContentType,
    { name: string; description: string; endpoint: string; sections: string[] }
> = {
    career_brand: {
        name: 'Career Brand',
        description: 'Upload one of your 9 brand framework sections',
        endpoint: '/documents/career-brand',
        sections: ['North Star', 'Values', 'Positioning Statement', 'Signature Capability', 'Impact Story'],
    },
    career_brand_full: {
        name: 'Career Brand (Full Document)',
        description: 'Upload your complete Career Brand document - automatically splits by H1 headers',
        endpoint: '/documents/career-brand/full',
        sections: [],
    },
    career_path: {
        name: 'Career Path',
        description: 'Upload a career trajectory or milestones document',
        endpoint: '/documents/career-paths',
        sections: ['Milestones', 'Growth Themes', 'Skill Gaps', 'Target Roles'],
    },
    job_search_strategy: {
        name: 'Job Search Strategy',
        description: 'Upload a strategy or playbook document',
        endpoint: '/documents/job-search-strategies',
        sections: ['Networking', 'Applications', 'Referrals', 'Interview Prep'],
    },
};

const STATUS_OPTIONS = [
    { value: 'draft', label: 'Draft' },
    { value: 'in_review', label: 'In Review' },
    { value: 'approved', label: 'Approved' },
] as const;

const TABS: { id: TabKey; label: string }[] = [
    { id: 'narratives', label: 'Narratives' },
    { id: 'proofPoints', label: 'Proof Points' },
    { id: 'resumes', label: 'Resumes' },
];

const parseCsv = (value: string): string[] =>
    value
        .split(',')
        .map(entry => entry.trim())
        .filter(Boolean);

interface DocumentViewerProps {
    strategicNarratives: StrategicNarrative[];
    selectedNarrativeId: string;
    onSelectNarrative: (id: string) => void;
    documents: UploadedDocument[];
    isLoading: boolean;
    onRefresh: () => void;
}

const DocumentViewer = ({
    strategicNarratives,
    selectedNarrativeId,
    onSelectNarrative,
    documents,
    isLoading,
    onRefresh,
}: DocumentViewerProps) => {
    const [showHistory, setShowHistory] = useState(false);
    const [collectionFilter, setCollectionFilter] = useState<string>('all');
    const [detailDocument, setDetailDocument] = useState<UploadedDocument | null>(null);
    const [detailData, setDetailData] = useState<DocumentDetail | null>(null);
    const [isDetailOpen, setIsDetailOpen] = useState(false);
    const [isDetailLoading, setIsDetailLoading] = useState(false);
    const { addToast } = useToast();

    const handleDelete = async (doc: UploadedDocument) => {
        if (window.confirm('Are you sure you want to delete this document?')) {
            try {
                await apiService.deleteUploadedDocument(doc.id);
                addToast('Document deleted', 'success');
                onRefresh();
            } catch (error) {
                addToast('Failed to delete document', 'error');
            }
        }
    };

    const closeDetail = () => {
        setIsDetailOpen(false);
        setDetailData(null);
        setDetailDocument(null);
    };

    const handleView = async (doc: UploadedDocument) => {
        setDetailDocument(doc);
        setIsDetailOpen(true);
        setIsDetailLoading(true);
        setDetailData(null);
        try {
            const detail = await apiService.getDocumentDetail(doc.collection_name || doc.content_type, doc.id);
            setDetailData(detail);
        } catch (error) {
            console.error(error);
            addToast('Failed to load document details', 'error');
            closeDetail();
        } finally {
            setIsDetailLoading(false);
        }
    };

    const collectionOptions = useMemo(() => {
        const set = new Set<string>();
        documents.forEach(doc => {
            const key = doc.collection_name || doc.content_type;
            if (key) {
                set.add(key);
            }
        });
        return Array.from(set).sort((a, b) => a.localeCompare(b));
    }, [documents]);

    const displayedDocuments = useMemo(() => {
        if (showHistory) {
            return documents;
        }

        const latestDocs = new Map<string, UploadedDocument>();
        for (const doc of documents) {
            const key = `${doc.collection_name || doc.content_type}-${doc.section}-${doc.metadata?.job_target ?? ''}`;
            const existing = latestDocs.get(key);
            const docTimestamp = new Date(doc.metadata?.updated_at ?? doc.created_at).getTime();
            if (!existing) {
                latestDocs.set(key, doc);
                continue;
            }

            const existingTimestamp = new Date(existing.metadata?.updated_at ?? existing.created_at).getTime();
            if (doc.metadata?.is_latest || docTimestamp > existingTimestamp) {
                latestDocs.set(key, doc);
            }
        }
        return Array.from(latestDocs.values());
    }, [documents, showHistory]);

    const filteredDocuments = useMemo(() => {
        if (collectionFilter === 'all') {
            return displayedDocuments;
        }
        return displayedDocuments.filter(
            doc => (doc.collection_name || doc.content_type) === collectionFilter,
        );
    }, [collectionFilter, displayedDocuments]);

    return (
        <div className="space-y-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <select
                    value={selectedNarrativeId}
                    onChange={e => onSelectNarrative(e.target.value)}
                    className="w-full max-w-xs p-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700"
                >
                    <option value="">Select a Narrative...</option>
                    {strategicNarratives.map(n => (
                        <option key={n.narrative_id} value={n.narrative_id}>
                            {n.narrative_name}
                        </option>
                    ))}
                </select>
                <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                    <input
                        type="checkbox"
                        checked={showHistory}
                        onChange={e => setShowHistory(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    Show History
                </label>
                <select
                    value={collectionFilter}
                    onChange={e => setCollectionFilter(e.target.value)}
                    className="w-full max-w-xs p-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700"
                >
                    <option value="all">All Collections</option>
                    {collectionOptions.map(option => (
                        <option key={option} value={option}>
                            {option}
                        </option>
                    ))}
                </select>
            </div>
            {isLoading ? (
                <p>Loading documents...</p>
            ) : (
                <div className="space-y-3">
                    {filteredDocuments.map(doc => (
                        <div
                            key={doc.id}
                            className="p-4 bg-slate-100 dark:bg-slate-700/50 rounded-lg flex flex-col gap-3 md:flex-row md:items-center md:justify-between"
                        >
                            <div className="space-y-1">
                                <p className="font-semibold text-slate-900 dark:text-slate-100">{doc.title}</p>
                                <p className="text-xs text-slate-500 dark:text-slate-300">
                                    {doc.content_type} / {doc.section || 'General'} / {new Date(doc.created_at).toLocaleString()}
                                </p>
                                <div className="flex flex-wrap gap-2 text-xs">
                                    {doc.metadata?.status && (
                                        <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200 px-2 py-1">
                                            <RocketLaunchIcon className="h-3 w-3" /> Status: {doc.metadata.status}
                                        </span>
                                    )}
                                    {doc.metadata?.is_latest && (
                                        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 text-green-800 dark:bg-green-900/60 dark:text-green-200 px-2 py-1">
                                            <CheckIcon className="h-3 w-3" /> Latest
                                        </span>
                                    )}
                                    {doc.collection_name && (
                                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-200 text-slate-700 dark:bg-slate-600 dark:text-slate-100 px-2 py-1">
                                            {doc.collection_name}
                                        </span>
                                    )}
                                    {doc.metadata?.selected_proof_points && doc.metadata.selected_proof_points.length > 0 && (
                                        <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/60 dark:text-purple-200 px-2 py-1">
                                            {doc.metadata.selected_proof_points.length} proof point(s)
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleView(doc)}
                                    className="self-start md:self-auto px-3 py-2 text-sm font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700"
                                >
                                    View
                                </button>
                                <button
                                    onClick={() => handleDelete(doc)}
                                    className="self-start md:self-auto p-2 text-red-500 hover:text-red-400"
                                    aria-label={`Delete ${doc.title}`}
                                >
                                    <TrashIcon className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                    {documents.length === 0 && selectedNarrativeId && (
                        <p className="text-center text-sm text-slate-500 py-4">No documents found for this narrative.</p>
                    )}
                </div>
            )}

            {isDetailOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                            <div>
                                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                                    {detailDocument?.title || 'Document Details'}
                                </h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                    {(detailDocument?.collection_name || detailDocument?.content_type) ?? ''}
                                    {detailData?.created_at && ` • ${new Date(detailData.created_at).toLocaleString()}`}
                                    {typeof detailData?.chunk_count === 'number' && ` • ${detailData.chunk_count} chunk(s)`}
                                </p>
                            </div>
                            <button
                                onClick={closeDetail}
                                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xl"
                                aria-label="Close document detail"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
                            {isDetailLoading ? (
                                <p className="text-sm text-slate-500">Loading document details…</p>
                            ) : detailData ? (
                                <>
                                    <section>
                                        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 uppercase tracking-wide">Metadata</h4>
                                        <div className="mt-2 space-y-2 text-sm">
                                            {Object.entries(detailData.metadata || {}).map(([key, value]) => (
                                                <div key={key} className="border border-slate-200 dark:border-slate-700 rounded-md px-3 py-2">
                                                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{key}</p>
                                                    <pre className="mt-1 whitespace-pre-wrap break-words text-slate-800 dark:text-slate-100 text-sm">
                                                        {typeof value === 'string'
                                                            ? value
                                                            : JSON.stringify(value, null, 2)}
                                                    </pre>
                                                </div>
                                            ))}
                                            {(!detailData.metadata || Object.keys(detailData.metadata).length === 0) && (
                                                <p className="text-slate-500">No metadata available.</p>
                                            )}
                                        </div>
                                    </section>
                                    <section>
                                        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 uppercase tracking-wide">Content</h4>
                                        <pre className="mt-2 whitespace-pre-wrap break-words bg-slate-50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-700 rounded-md px-3 py-3 text-sm text-slate-900 dark:text-slate-100">
                                            {detailData.content || 'No content available.'}
                                        </pre>
                                    </section>
                                </>
                            ) : (
                                <p className="text-sm text-slate-500">Document details could not be loaded.</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

interface ChromaUploadViewProps {
    strategicNarratives: StrategicNarrative[];
    activeNarrativeId: string | null;
}

export const ChromaUploadView = ({ strategicNarratives, activeNarrativeId }: ChromaUploadViewProps) => {
    const [activeTab, setActiveTab] = useState<TabKey>('narratives');
    const [narrativeStep, setNarrativeStep] = useState<'select' | 'details'>('select');
    const [contentType, setContentType] = useState<NarrativeContentType | null>(null);
    const [narrativeId, setNarrativeId] = useState(activeNarrativeId || '');
    const [section, setSection] = useState('');
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [narrativeErrors, setNarrativeErrors] = useState<Record<string, string>>({});

    const [documents, setDocuments] = useState<UploadedDocument[]>([]);
    const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);

    const [proofContent, setProofContent] = useState('');
    const [proofRole, setProofRole] = useState('');
    const [proofLocation, setProofLocation] = useState('');
    const [proofStartDate, setProofStartDate] = useState('');
    const [proofEndDate, setProofEndDate] = useState('');
    const [proofIsCurrent, setProofIsCurrent] = useState(false);
    const [proofCompany, setProofCompany] = useState('');
    const [proofSkills, setProofSkills] = useState('');
    const [proofKeywords, setProofKeywords] = useState('');
    const [proofArchitecture, setProofArchitecture] = useState('');
    const [proofErrors, setProofErrors] = useState<Record<string, string>>({});
    const [isSavingProof, setIsSavingProof] = useState(false);

    const [resumeTitle, setResumeTitle] = useState('');
    const [resumeContent, setResumeContent] = useState('');
    const [resumeTarget, setResumeTarget] = useState('');
    const [resumeSkills, setResumeSkills] = useState('');
    const [resumeStatus, setResumeStatus] = useState<typeof STATUS_OPTIONS[number]['value']>('draft');
    const [resumeSelectedProofs, setResumeSelectedProofs] = useState<string[]>([]);
    const [resumeIsLatest, setResumeIsLatest] = useState(true);
    const [resumeApprovedBy, setResumeApprovedBy] = useState('');
    const [resumeApprovalNotes, setResumeApprovalNotes] = useState('');
    const [resumeErrors, setResumeErrors] = useState<Record<string, string>>({});
    const [isSavingResume, setIsSavingResume] = useState(false);

    const [approvalResumeId, setApprovalResumeId] = useState('');
    const [approvalStatus, setApprovalStatus] = useState<typeof STATUS_OPTIONS[number]['value']>('approved');
    const [approvalProofs, setApprovalProofs] = useState<string[]>([]);
    const [approvalIsLatest, setApprovalIsLatest] = useState(true);
    const [approvalApprovedBy, setApprovalApprovedBy] = useState('');
    const [approvalNotes, setApprovalNotes] = useState('');
    const [approvalErrors, setApprovalErrors] = useState<Record<string, string>>({});
    const [isSubmittingApproval, setIsSubmittingApproval] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const { addToast } = useToast();

    useEffect(() => {
        if (activeNarrativeId) {
            setNarrativeId(activeNarrativeId);
        } else if (!narrativeId && strategicNarratives.length > 0) {
            setNarrativeId(strategicNarratives[0].narrative_id);
        }
    }, [activeNarrativeId, narrativeId, strategicNarratives]);

    const refreshDocuments = useCallback(async () => {
        if (!narrativeId) {
            setDocuments([]);
            return;
        }
        setIsLoadingDocuments(true);
        try {
            const docs = await apiService.getUploadedDocuments(narrativeId);
            setDocuments(docs);
        } catch (error) {
            addToast('Failed to load documents', 'error');
        } finally {
            setIsLoadingDocuments(false);
        }
    }, [narrativeId, addToast]);

    useEffect(() => {
        refreshDocuments();
    }, [refreshDocuments]);

    useEffect(() => {
        const selectedDoc = documents.find(doc => doc.id === approvalResumeId);
        if (selectedDoc) {
            setApprovalStatus((selectedDoc.metadata?.status as typeof STATUS_OPTIONS[number]['value']) || 'draft');
            setApprovalIsLatest(Boolean(selectedDoc.metadata?.is_latest));
            setApprovalProofs(selectedDoc.metadata?.selected_proof_points || []);
            setApprovalNotes((selectedDoc.metadata?.approval_notes as string) || '');
            setApprovalApprovedBy((selectedDoc.metadata?.approved_by as string) || '');
        }
    }, [approvalResumeId, documents]);

    const availableProofPoints = useMemo(
        () => documents.filter(doc => doc.content_type === 'proof_points'),
        [documents]
    );

    const availableResumes = useMemo(
        () => documents.filter(doc => doc.content_type === 'resumes'),
        [documents]
    );

    const resetApprovalForm = () => {
        setApprovalResumeId('');
        setApprovalStatus('approved');
        setApprovalIsLatest(true);
        setApprovalProofs([]);
        setApprovalNotes('');
        setApprovalApprovedBy('');
        setApprovalErrors({});
    };

    const handleNarrativeSelect = (id: string) => {
        setNarrativeId(id);
        resetApprovalForm();
    };

    const handleTypeSelect = (type: NarrativeContentType) => {
        setContentType(type);
        setSection(NARRATIVE_CONTENT_TYPES[type].sections[0] || '');
        setNarrativeStep('details');
    };

    const handleNarrativeBack = () => {
        setContentType(null);
        setNarrativeStep('select');
        setTitle('');
        setContent('');
        setFile(null);
        setNarrativeErrors({});
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const validateNarrative = () => {
        const errors: Record<string, string> = {};
        if (!narrativeId) {
            errors.narrative = 'Narrative is required.';
        }
        if (contentType && contentType !== 'career_brand_full' && !title.trim()) {
            errors.title = 'Title is required.';
        }
        if (contentType && contentType !== 'career_brand_full' && !content.trim()) {
            errors.content = 'Content is required.';
        }
        if (contentType === 'career_brand_full' && !file) {
            errors.file = 'A file is required for full document uploads.';
        }
        setNarrativeErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleNarrativeSubmit = async () => {
        if (!contentType) {
            return;
        }
        if (!validateNarrative()) return;

        setIsUploading(true);
        try {
            let result;
            if (contentType === 'career_brand_full' && file) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('profile_id', narrativeId);
                formData.append('metadata', JSON.stringify({ uploaded_at: new Date().toISOString() }));

                const fastApiBase = FASTAPI_BASE_URL.replace(/\/+$/u, '') || '/api';
                const url = `${fastApiBase}${NARRATIVE_CONTENT_TYPES[contentType].endpoint}`;
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                });
                const data = await response.json();
                if (!response.ok || data.success === false) {
                    throw new Error(data.detail || data.message || 'Upload failed');
                }
                result = data;
            } else {
                const payload = {
                    profile_id: narrativeId,
                    section,
                    title,
                    content,
                    metadata: { uploaded_at: new Date().toISOString() },
                };
                switch (contentType) {
                    case 'career_brand':
                        result = await apiService.uploadCareerBrand(payload);
                        break;
                    case 'career_path':
                        result = await apiService.uploadCareerPath(payload);
                        break;
                    case 'job_search_strategy':
                        result = await apiService.uploadJobSearchStrategy(payload);
                        break;
                    default:
                        throw new Error('Unsupported content type');
                }
            }

            if (!result || result.success === false) {
                throw new Error(result?.message || 'Upload failed');
            }

            addToast('Upload successful!', 'success');
            handleNarrativeBack();
            refreshDocuments();
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Upload failed', 'error');
        } finally {
            setIsUploading(false);
        }
    };

    const validateProofPoint = () => {
        const errors: Record<string, string> = {};
        if (!narrativeId) errors.narrative = 'Narrative is required.';
        if (!proofContent.trim()) errors.content = 'Content is required.';
        if (!proofRole.trim()) errors.role = 'Role title is required.';
        if (!proofLocation.trim()) errors.location = 'Location is required.';
        if (!proofStartDate) errors.start_date = 'Start date is required.';
        if (!proofIsCurrent && !proofEndDate) errors.end_date = 'End date is required unless current.';
        if (!proofCompany.trim()) errors.company = 'Company is required.';
        setProofErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleProofPointSubmit = async () => {
        if (!validateProofPoint()) return;
        setIsSavingProof(true);
        try {
            const computedTitleParts = [proofCompany.trim(), proofRole.trim()].filter(Boolean);
            const computedTitle = computedTitleParts.join(' - ') || proofCompany.trim() || proofRole.trim();

            const jobMetadata: Record<string, unknown> = {};
            if (proofKeywords.trim()) {
                jobMetadata.keywords = parseCsv(proofKeywords);
            }
            if (proofArchitecture.trim()) {
                jobMetadata.architecture = parseCsv(proofArchitecture);
            }

            const payload = {
                profile_id: narrativeId,
                role_title: proofRole.trim(),
                location: proofLocation.trim(),
                start_date: proofStartDate,
                end_date: proofIsCurrent ? null : proofEndDate || null,
                is_current: proofIsCurrent,
                company: proofCompany.trim(),
                title: computedTitle,
                content: proofContent.trim(),
                impact_tags: parseCsv(proofSkills),
                job_metadata: Object.keys(jobMetadata).length > 0 ? jobMetadata : undefined,
            };
            const response = await apiService.createProofPoint(payload);
            if (response.status !== 'success') {
                throw new Error(response.error || response.message || 'Failed to save proof point');
            }
            addToast('Proof point saved!', 'success');
            setProofContent('');
            setProofRole('');
            setProofLocation('');
            setProofStartDate('');
            setProofEndDate('');
            setProofIsCurrent(false);
            setProofCompany('');
            setProofSkills('');
            setProofKeywords('');
            setProofArchitecture('');
            refreshDocuments();
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Failed to save proof point', 'error');
        } finally {
            setIsSavingProof(false);
        }
    };

    const validateResumeDraft = () => {
        const errors: Record<string, string> = {};
        if (!narrativeId) errors.narrative = 'Narrative is required.';
        if (!resumeTitle.trim()) errors.title = 'Title is required.';
        if (!resumeContent.trim()) errors.content = 'Content is required.';
        setResumeErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleResumeDraftSubmit = async () => {
        if (!validateResumeDraft()) return;
        setIsSavingResume(true);
        try {
            const payload = {
                profile_id: narrativeId,
                title: resumeTitle,
                content: resumeContent,
                job_target: resumeTarget || undefined,
                status: resumeStatus,
                selected_proof_points: resumeSelectedProofs,
                is_latest: resumeIsLatest,
                additional_metadata: resumeSkills ? { skills: parseCsv(resumeSkills) } : undefined,
                approved_by: resumeStatus === 'approved' ? resumeApprovedBy || undefined : undefined,
                approval_notes: resumeApprovalNotes || undefined,
                approved_at:
                    resumeStatus === 'approved' && (resumeApprovedBy || resumeApprovalNotes)
                        ? new Date().toISOString()
                        : undefined,
            };
            const response = await apiService.createResumeDocument(payload);
            if (response.status !== 'success') {
                throw new Error(response.error || response.message || 'Failed to save resume');
            }
            addToast('Resume draft saved!', 'success');
            setResumeTitle('');
            setResumeContent('');
            setResumeTarget('');
            setResumeSkills('');
            setResumeSelectedProofs([]);
            setResumeIsLatest(true);
            setResumeApprovedBy('');
            setResumeApprovalNotes('');
            setResumeStatus('draft');
            refreshDocuments();
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Failed to save resume', 'error');
        } finally {
            setIsSavingResume(false);
        }
    };

    const validateApproval = () => {
        const errors: Record<string, string> = {};
        if (!approvalResumeId) errors.resume = 'Select a resume to update.';
        if (approvalStatus === 'approved' && !approvalApprovedBy.trim()) {
            errors.approved_by = 'Reviewer email is required for approval.';
        }
        setApprovalErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleApprovalSubmit = async () => {
        if (!validateApproval()) return;
        setIsSubmittingApproval(true);
        try {
            const payload = {
                status: approvalStatus,
                selected_proof_points: approvalProofs,
                approved_by: approvalApprovedBy || undefined,
                approval_notes: approvalNotes || undefined,
                is_latest: approvalIsLatest,
                approved_at: approvalStatus === 'approved' ? new Date().toISOString() : undefined,
            };
            const response = await apiService.updateResumeDocument(approvalResumeId, payload);
            if (response.status !== 'success') {
                throw new Error(response.error || response.message || 'Failed to update resume');
            }
            addToast('Resume metadata updated!', 'success');
            refreshDocuments();
        } catch (error) {
            addToast(error instanceof Error ? error.message : 'Failed to update resume', 'error');
        } finally {
            setIsSubmittingApproval(false);
        }
    };

    const inputClass = 'w-full p-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700';
    const labelClass = 'block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1';

    const renderProofCheckboxes = (
        selected: string[],
        toggle: (id: string) => void,
    ) => (
        <div className="space-y-2">
            {availableProofPoints.length === 0 && <p className="text-xs text-slate-500">No proof points available yet.</p>}
            {availableProofPoints.map(point => (
                <label key={point.id} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                    <input
                        type="checkbox"
                        checked={selected.includes(point.id)}
                        onChange={() => toggle(point.id)}
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span>{point.title}</span>
                </label>
            ))}
        </div>
    );

    const toggleResumeProof = (id: string) => {
        setResumeSelectedProofs(prev => (prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]));
    };

    const toggleApprovalProof = (id: string) => {
        setApprovalProofs(prev => (prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]));
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Document Uploader</h1>
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700 space-y-6">
                <div className="flex flex-wrap gap-2">
                    {TABS.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors ${
                                activeTab === tab.id
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200'
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                <div>
                    <label htmlFor="narrative-select" className={labelClass}>
                        Active Narrative
                    </label>
                    <select
                        id="narrative-select"
                        value={narrativeId}
                        onChange={e => handleNarrativeSelect(e.target.value)}
                        className={inputClass}
                    >
                        <option value="">Select a narrative...</option>
                        {strategicNarratives.map(n => (
                            <option key={n.narrative_id} value={n.narrative_id}>
                                {n.narrative_name}
                            </option>
                        ))}
                    </select>
                    {activeTab === 'narratives' && narrativeErrors.narrative && (
                        <p className="text-xs text-red-500 mt-1">{narrativeErrors.narrative}</p>
                    )}
                    {activeTab === 'proofPoints' && proofErrors.narrative && (
                        <p className="text-xs text-red-500 mt-1">{proofErrors.narrative}</p>
                    )}
                    {activeTab === 'resumes' && (resumeErrors.narrative || approvalErrors.narrative) && (
                        <p className="text-xs text-red-500 mt-1">{resumeErrors.narrative || approvalErrors.narrative}</p>
                    )}
                </div>

                {activeTab === 'narratives' && (
                    <div className="space-y-6">
                        {narrativeStep === 'select' ? (
                            <>
                                <h2 className="text-xl font-semibold">What are you uploading?</h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {Object.entries(NARRATIVE_CONTENT_TYPES).map(([key, value]) => (
                                        <button
                                            key={key}
                                            onClick={() => handleTypeSelect(key as NarrativeContentType)}
                                            className="text-left p-4 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                                        >
                                            <h3 className="font-semibold text-slate-800 dark:text-slate-200">{value.name}</h3>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">{value.description}</p>
                                        </button>
                                    ))}
                                </div>
                            </>
                        ) : (
                            contentType && (
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center">
                                        <h2 className="text-xl font-semibold">
                                            Details for: <span className="text-blue-600 dark:text-blue-400">{NARRATIVE_CONTENT_TYPES[contentType].name}</span>
                                        </h2>
                                        <button
                                            onClick={handleNarrativeBack}
                                            className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
                                        >
                                            <ArrowUturnLeftIcon className="h-4 w-4" /> Back
                                        </button>
                                    </div>

                                    {contentType !== 'career_brand_full' && (
                                        <div>
                                            <label htmlFor="section" className={labelClass}>
                                                Section
                                            </label>
                                            <select
                                                id="section"
                                                value={section}
                                                onChange={e => setSection(e.target.value)}
                                                className={inputClass}
                                            >
                                                {NARRATIVE_CONTENT_TYPES[contentType].sections.map(s => (
                                                    <option key={s} value={s}>
                                                        {s}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    )}

                                    {contentType !== 'career_brand_full' && (
                                        <div>
                                            <label htmlFor="narrative-title" className={labelClass}>
                                                Title
                                            </label>
                                            <input
                                                id="narrative-title"
                                                type="text"
                                                value={title}
                                                onChange={e => setTitle(e.target.value)}
                                                className={inputClass}
                                            />
                                            {narrativeErrors.title && <p className="text-xs text-red-500 mt-1">{narrativeErrors.title}</p>}
                                        </div>
                                    )}

                                    {contentType === 'career_brand_full' ? (
                                        <div>
                                            <label htmlFor="career-brand-file" className={labelClass}>
                                                Full Career Brand Document
                                            </label>
                                            <input
                                                ref={fileInputRef}
                                                id="career-brand-file"
                                                type="file"
                                                accept=".txt,.md,.markdown"
                                                onChange={e => setFile(e.target.files ? e.target.files[0] : null)}
                                                className="text-sm"
                                            />
                                            <p className="text-xs text-slate-500 mt-1">
                                                Upload your complete Career Brand document. Each H1 header (#) will be parsed as a separate section.
                                            </p>
                                            {narrativeErrors.file && <p className="text-xs text-red-500 mt-1">{narrativeErrors.file}</p>}
                                        </div>
                                    ) : (
                                        <div>
                                            <label htmlFor="narrative-content" className={labelClass}>
                                                Content
                                            </label>
                                            <textarea
                                                id="narrative-content"
                                                value={content}
                                                onChange={e => setContent(e.target.value)}
                                                rows={8}
                                                className={inputClass}
                                            />
                                            {narrativeErrors.content && <p className="text-xs text-red-500 mt-1">{narrativeErrors.content}</p>}
                                        </div>
                                    )}

                                    <button
                                        onClick={handleNarrativeSubmit}
                                        disabled={isUploading}
                                        className="w-full py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:bg-blue-400"
                                    >
                                        {isUploading ? 'Uploading...' : 'Upload'}
                                    </button>
                                </div>
                            )
                        )}
                    </div>
                )}

                {activeTab === 'proofPoints' && (
                    <div className="space-y-4">
                        <h2 className="text-xl font-semibold">Create Proof Point</h2>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div>
                                <label htmlFor="proof-role" className={labelClass}>
                                    Role Title
                                </label>
                                <input
                                    id="proof-role"
                                    type="text"
                                    value={proofRole}
                                    onChange={e => setProofRole(e.target.value)}
                                    className={inputClass}
                                />
                                {proofErrors.role && <p className="text-xs text-red-500 mt-1">{proofErrors.role}</p>}
                            </div>
                            <div>
                                <label htmlFor="proof-company" className={labelClass}>
                                    Company
                                </label>
                                <input
                                    id="proof-company"
                                    type="text"
                                    value={proofCompany}
                                    onChange={e => setProofCompany(e.target.value)}
                                    className={inputClass}
                                />
                                {proofErrors.company && <p className="text-xs text-red-500 mt-1">{proofErrors.company}</p>}
                            </div>
                        </div>
                        <div>
                            <label htmlFor="proof-location" className={labelClass}>
                                Location
                            </label>
                            <input
                                id="proof-location"
                                type="text"
                                value={proofLocation}
                                onChange={e => setProofLocation(e.target.value)}
                                className={inputClass}
                            />
                            {proofErrors.location && (
                                <p className="text-xs text-red-500 mt-1">{proofErrors.location}</p>
                            )}
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div>
                                <label htmlFor="proof-start-date" className={labelClass}>
                                    Start Date
                                </label>
                                <input
                                    id="proof-start-date"
                                    type="date"
                                    value={proofStartDate}
                                    onChange={e => setProofStartDate(e.target.value)}
                                    className={inputClass}
                                />
                                {proofErrors.start_date && (
                                    <p className="text-xs text-red-500 mt-1">{proofErrors.start_date}</p>
                                )}
                            </div>
                            <div>
                                <div className="flex items-center justify-between">
                                    <label htmlFor="proof-end-date" className={labelClass}>
                                        End Date
                                    </label>
                                    <label className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
                                        <input
                                            type="checkbox"
                                            checked={proofIsCurrent}
                                            onChange={event => {
                                                const checked = event.target.checked;
                                                setProofIsCurrent(checked);
                                                if (checked) {
                                                    setProofEndDate('');
                                                }
                                            }}
                                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        Current Role
                                    </label>
                                </div>
                                <input
                                    id="proof-end-date"
                                    type="date"
                                    value={proofEndDate}
                                    onChange={e => setProofEndDate(e.target.value)}
                                    className={inputClass}
                                    disabled={proofIsCurrent}
                                />
                                {proofErrors.end_date && (
                                    <p className="text-xs text-red-500 mt-1">{proofErrors.end_date}</p>
                                )}
                            </div>
                        </div>
                        <div>
                            <label htmlFor="proof-skills" className={labelClass}>
                                Skills (comma separated)
                            </label>
                            <input
                                id="proof-skills"
                                type="text"
                                value={proofSkills}
                                onChange={e => setProofSkills(e.target.value)}
                                className={inputClass}
                            />
                        </div>
                        <div>
                            <label htmlFor="proof-keywords" className={labelClass}>
                                Keywords (comma separated)
                            </label>
                            <input
                                id="proof-keywords"
                                type="text"
                                value={proofKeywords}
                                onChange={e => setProofKeywords(e.target.value)}
                                className={inputClass}
                            />
                        </div>
                        <div>
                            <label htmlFor="proof-architecture" className={labelClass}>
                                Architecture (comma separated)
                            </label>
                            <input
                                id="proof-architecture"
                                type="text"
                                value={proofArchitecture}
                                onChange={e => setProofArchitecture(e.target.value)}
                                className={inputClass}
                            />
                        </div>
                        <div>
                            <label htmlFor="proof-content" className={labelClass}>
                                Content
                            </label>
                            <textarea
                                id="proof-content"
                                value={proofContent}
                                onChange={e => setProofContent(e.target.value)}
                                rows={6}
                                className={inputClass}
                            />
                            {proofErrors.content && <p className="text-xs text-red-500 mt-1">{proofErrors.content}</p>}
                        </div>
                        <button
                            onClick={handleProofPointSubmit}
                            disabled={isSavingProof}
                            className="w-full py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:bg-blue-400"
                        >
                            {isSavingProof ? 'Saving...' : 'Save Proof Point'}
                        </button>
                    </div>
                )}

                {activeTab === 'resumes' && (
                    <div className="space-y-8">
                        <div className="space-y-4">
                            <h2 className="text-xl font-semibold">Upload Resume Draft</h2>
                            <div>
                                <label htmlFor="resume-title" className={labelClass}>
                                    Title
                                </label>
                                <input
                                    id="resume-title"
                                    type="text"
                                    value={resumeTitle}
                                    onChange={e => setResumeTitle(e.target.value)}
                                    className={inputClass}
                                />
                                {resumeErrors.title && <p className="text-xs text-red-500 mt-1">{resumeErrors.title}</p>}
                            </div>
                            <div>
                                <label htmlFor="resume-target" className={labelClass}>
                                    Role / Company Target
                                </label>
                                <input
                                    id="resume-target"
                                    type="text"
                                    value={resumeTarget}
                                    onChange={e => setResumeTarget(e.target.value)}
                                    className={inputClass}
                                    placeholder="e.g. Principal PM @ Acme"
                                />
                            </div>
                            <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                    <label htmlFor="resume-status" className={labelClass}>
                                        Status
                                    </label>
                                    <select
                                        id="resume-status"
                                        value={resumeStatus}
                                        onChange={e => setResumeStatus(e.target.value as typeof STATUS_OPTIONS[number]['value'])}
                                        className={inputClass}
                                    >
                                        {STATUS_OPTIONS.map(option => (
                                            <option key={option.value} value={option.value}>
                                                {option.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div className="flex items-center gap-2 mt-6 md:mt-8">
                                    <input
                                        id="resume-latest"
                                        type="checkbox"
                                        checked={resumeIsLatest}
                                        onChange={e => setResumeIsLatest(e.target.checked)}
                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                    <label htmlFor="resume-latest" className="text-sm text-slate-600 dark:text-slate-300">
                                        Mark as latest version
                                    </label>
                                </div>
                            </div>
                            <div>
                                <label className={labelClass}>Selected Proof Points</label>
                                {renderProofCheckboxes(resumeSelectedProofs, toggleResumeProof)}
                            </div>
                            <div>
                                <label htmlFor="resume-skills" className={labelClass}>
                                    Skills Highlighted (comma separated)
                                </label>
                                <input
                                    id="resume-skills"
                                    type="text"
                                    value={resumeSkills}
                                    onChange={e => setResumeSkills(e.target.value)}
                                    className={inputClass}
                                />
                            </div>
                            <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                    <label htmlFor="resume-approved-by" className={labelClass}>
                                        Reviewer Email
                                    </label>
                                    <input
                                        id="resume-approved-by"
                                        type="email"
                                        value={resumeApprovedBy}
                                        onChange={e => setResumeApprovedBy(e.target.value)}
                                        className={inputClass}
                                    />
                                </div>
                                <div>
                                    <label htmlFor="resume-notes" className={labelClass}>
                                        Reviewer Notes
                                    </label>
                                    <input
                                        id="resume-notes"
                                        type="text"
                                        value={resumeApprovalNotes}
                                        onChange={e => setResumeApprovalNotes(e.target.value)}
                                        className={inputClass}
                                    />
                                </div>
                            </div>
                            <div>
                                <label htmlFor="resume-content" className={labelClass}>
                                    Resume Content
                                </label>
                                <textarea
                                    id="resume-content"
                                    value={resumeContent}
                                    onChange={e => setResumeContent(e.target.value)}
                                    rows={10}
                                    className={inputClass}
                                />
                                {resumeErrors.content && <p className="text-xs text-red-500 mt-1">{resumeErrors.content}</p>}
                            </div>
                            <button
                                onClick={handleResumeDraftSubmit}
                                disabled={isSavingResume}
                                className="w-full py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:bg-blue-400"
                            >
                                {isSavingResume ? 'Saving...' : 'Upload Resume Draft'}
                            </button>
                        </div>

                        <div className="space-y-4">
                            <h2 className="text-xl font-semibold">Approval & Status Updates</h2>
                            <div>
                                <label htmlFor="approval-resume" className={labelClass}>
                                    Select Resume
                                </label>
                                <select
                                    id="approval-resume"
                                    value={approvalResumeId}
                                    onChange={e => setApprovalResumeId(e.target.value)}
                                    className={inputClass}
                                >
                                    <option value="">Choose a resume...</option>
                                    {availableResumes.map(resume => (
                                        <option key={resume.id} value={resume.id}>
                                            {resume.title}
                                        </option>
                                    ))}
                                </select>
                                {approvalErrors.resume && <p className="text-xs text-red-500 mt-1">{approvalErrors.resume}</p>}
                            </div>
                            <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                    <label htmlFor="approval-status" className={labelClass}>
                                        Status
                                    </label>
                                    <select
                                        id="approval-status"
                                        value={approvalStatus}
                                        onChange={e => setApprovalStatus(e.target.value as typeof STATUS_OPTIONS[number]['value'])}
                                        className={inputClass}
                                    >
                                        {STATUS_OPTIONS.map(option => (
                                            <option key={option.value} value={option.value}>
                                                {option.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div className="flex items-center gap-2 mt-6 md:mt-8">
                                    <input
                                        id="approval-latest"
                                        type="checkbox"
                                        checked={approvalIsLatest}
                                        onChange={e => setApprovalIsLatest(e.target.checked)}
                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                    <label htmlFor="approval-latest" className="text-sm text-slate-600 dark:text-slate-300">
                                        Mark as latest version
                                    </label>
                                </div>
                            </div>
                            <div>
                                <label className={labelClass}>Selected Proof Points</label>
                                {renderProofCheckboxes(approvalProofs, toggleApprovalProof)}
                            </div>
                            <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                    <label htmlFor="approval-by" className={labelClass}>
                                        Reviewer Email
                                    </label>
                                    <input
                                        id="approval-by"
                                        type="email"
                                        value={approvalApprovedBy}
                                        onChange={e => setApprovalApprovedBy(e.target.value)}
                                        className={inputClass}
                                    />
                                    {approvalErrors.approved_by && <p className="text-xs text-red-500 mt-1">{approvalErrors.approved_by}</p>}
                                </div>
                                <div>
                                    <label htmlFor="approval-notes" className={labelClass}>
                                        Reviewer Notes
                                    </label>
                                    <input
                                        id="approval-notes"
                                        type="text"
                                        value={approvalNotes}
                                        onChange={e => setApprovalNotes(e.target.value)}
                                        className={inputClass}
                                    />
                                </div>
                            </div>
                            <button
                                onClick={handleApprovalSubmit}
                                disabled={isSubmittingApproval}
                                className="w-full py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:bg-blue-400"
                            >
                                {isSubmittingApproval ? 'Updating...' : 'Submit Approval Update'}
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-semibold mb-4">View Uploaded Documents</h2>
                <DocumentViewer
                    strategicNarratives={strategicNarratives}
                    selectedNarrativeId={narrativeId}
                    onSelectNarrative={handleNarrativeSelect}
                    documents={documents}
                    isLoading={isLoadingDocuments}
                    onRefresh={refreshDocuments}
                />
            </div>
        </div>
    );
};

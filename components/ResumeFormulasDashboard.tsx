import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    StrategicNarrative,
    UploadedDocument,
} from '../types';
import * as apiService from '../services/apiService';
import { useToast } from '../hooks/useToast';
import {
    SparklesIcon,
    CheckBadgeIcon,
    ClockIcon,
    DocumentTextIcon,
    ChevronRightIcon,
    LoadingSpinner,
    PlusIcon,
    BuildingOfficeIcon,
    BoltIcon,
    CalendarIcon,
    MapPinIcon,
    TagIcon,
    TrashIcon,
} from './IconComponents';

interface ResumeFormulasDashboardProps {
    activeNarrative?: StrategicNarrative | null;
}

const parseCsv = (csv: string) => csv.split(',').map(s => s.trim()).filter(Boolean);

export const ResumeFormulasDashboard = ({ activeNarrative }: ResumeFormulasDashboardProps) => {
    const [documents, setDocuments] = useState<UploadedDocument[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedExpKey, setSelectedExpKey] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // Form State (Aligned with ChromaUploadView Proof Points)
    const [formData, setFormData] = useState({
        role: '',
        company: '',
        location: '',
        startDate: '',
        endDate: '',
        isCurrent: false,
        skills: '',
        keywords: '',
        architecture: '',
        content: '',
    });
    const [errors, setErrors] = useState<Record<string, string>>({});

    const { addToast } = useToast();

    const fetchDocuments = useCallback(async () => {
        setIsLoading(true);
        try {
            // Fetch all documents from proof_points collection directly
            const docs = await apiService.getCollectionDocuments('proof_points');
            setDocuments(docs);
        } catch (error) {
            addToast('Failed to load experiences', 'error');
        } finally {
            setIsLoading(false);
        }
    }, [addToast]);

    useEffect(() => {
        fetchDocuments();
    }, [fetchDocuments]);

    // Grouping logic: each company + role pair is a unique Experience
    const experiences = useMemo(() => {
        const groups: Record<string, UploadedDocument[]> = {};
        documents.forEach(doc => {
            const company = doc.metadata?.company || 'Unknown Company';
            const startDate = doc.metadata?.start_date || 'Unknown Date';
            const key = `${company}|${startDate}`;
            if (!groups[key]) groups[key] = [];
            groups[key].push(doc);
        });

        return Object.entries(groups).map(([key, docs]) => {
            // Sort by creation date or version to find the "active" one
            const sorted = docs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
            return {
                key,
                latest: sorted[0],
                versions: sorted,
            };
        }).sort((a, b) => {
            // Sort by start date if available
            const dateA = a.latest.metadata?.start_date ? new Date(a.latest.metadata.start_date as string).getTime() : 0;
            const dateB = b.latest.metadata?.start_date ? new Date(b.latest.metadata.start_date as string).getTime() : 0;
            return dateB - dateA;
        });
    }, [documents]);

    const handleEditExperience = async (expKey: string) => {
        const exp = experiences.find(e => e.key === expKey);
        if (exp) {
            setIsLoading(true);
            try {
                const detail = await apiService.getDocumentDetail(exp.latest.collection_name || 'proof_points', exp.latest.id);
                const meta = detail.metadata || {};
                const jobMeta = meta.job_metadata as Record<string, unknown> | undefined;
                setFormData({
                    role: (meta.role_title as string) || '',
                    company: (meta.company as string) || '',
                    location: (meta.location as string) || '',
                    startDate: (meta.start_date as string) || '',
                    endDate: (meta.end_date as string) || '',
                    isCurrent: Boolean(meta.is_current),
                    skills: Array.isArray(meta.impact_tags) ? meta.impact_tags.join(', ') : '',
                    keywords: Array.isArray(meta.job_keywords) ? (meta.job_keywords as string[]).join(', ') : (Array.isArray(jobMeta?.keywords) ? (jobMeta?.keywords as string[]).join(', ') : ''),
                    architecture: Array.isArray(meta.job_architecture) ? (meta.job_architecture as string[]).join(', ') : (Array.isArray(jobMeta?.architecture) ? (jobMeta?.architecture as string[]).join(', ') : ''),
                    content: detail.content || '',
                });
                setSelectedExpKey(expKey);
                setErrors({});
            } catch (error) {
                addToast('Failed to load formula details', 'error');
            } finally {
                setIsLoading(false);
            }
        }
    };

    const handleAddNew = () => {
        setFormData({
            role: '',
            company: '',
            location: '',
            startDate: '',
            endDate: '',
            isCurrent: false,
            skills: '',
            keywords: '',
            architecture: '',
            content: '',
        });
        setSelectedExpKey('new');
        setErrors({});
    };

    const handleDeleteExperience = async (e: React.MouseEvent, expKey: string) => {
        e.stopPropagation(); // Prevent opening the editor
        const exp = experiences.find(e => e.key === expKey);
        if (!exp) return;

        if (!window.confirm(`Are you sure you want to delete the experience at ${exp.latest.metadata?.company}? This will permanently remove all versioned formulas for this role.`)) {
            return;
        }

        try {
            const response = await apiService.deleteDocument('proof_points', exp.latest.id);
            if (response.status === 'success') {
                addToast('Experience deleted successfully', 'success');
                await fetchDocuments();
            } else {
                addToast(response.message || 'Failed to delete experience', 'error');
            }
        } catch (error) {
            console.error('Delete failed:', error);
            addToast('Failed to delete experience', 'error');
        }
    };

    const validate = () => {
        const newErrors: Record<string, string> = {};
        if (!formData.role.trim()) newErrors.role = 'Required';
        if (!formData.company.trim()) newErrors.company = 'Required';
        if (!formData.content.trim()) newErrors.content = 'Required';
        if (!formData.startDate) newErrors.startDate = 'Required';
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSave = async () => {
        // Use activeNarrative.narrative_id or fallback to USER_ID
        const profileId = activeNarrative?.narrative_id || '';
        if (!validate()) return;

        setIsSaving(true);
        try {
            const jobMetadata: Record<string, unknown> = {};
            if (formData.keywords) jobMetadata.keywords = parseCsv(formData.keywords);
            if (formData.architecture) jobMetadata.architecture = parseCsv(formData.architecture);

            const payload = {
                profile_id: profileId,
                role_title: formData.role.trim(),
                company: formData.company.trim(),
                location: formData.location.trim(),
                start_date: formData.startDate,
                end_date: formData.isCurrent ? null : formData.endDate || null,
                is_current: formData.isCurrent,
                title: `${formData.company} - ${formData.role}`,
                content: formData.content.trim(),
                impact_tags: parseCsv(formData.skills),
                job_metadata: Object.keys(jobMetadata).length > 0 ? jobMetadata : undefined,
            };

            const response = await apiService.createProofPoint(payload);
            if (response.status !== 'success') throw new Error(response.message);

            addToast('Experience formula synchronized successfully', 'success');
            await fetchDocuments();
            setSelectedExpKey(null);
        } catch (error) {
            console.error('Failed to save experience alignment:', error);
            addToast('Failed to save experience alignment', 'error');
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading && experiences.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-24">
                <LoadingSpinner className="w-12 h-12 text-blue-500" />
                <p className="mt-4 text-slate-500 font-bold uppercase tracking-widest text-xs">Aligning Job History...</p>
            </div>
        );
    }

    return (
        <div className="space-y-10 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-slate-200 dark:border-slate-800">
                <div className="max-w-2xl">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-blue-600 rounded-lg">
                            <DocumentTextIcon className="w-5 h-5 text-white" />
                        </div>
                        <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Experience Alignment</h2>
                    </div>
                    <p className="text-slate-500 dark:text-slate-400 font-medium leading-relaxed">
                        Ensure each experience in your job history has a single, high-fidelity active proof point. These formulas anchor your professional narrative for AI matching.
                    </p>
                </div>
                <button
                    onClick={handleAddNew}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-2xl shadow-xl shadow-blue-500/20 transition-all uppercase tracking-widest text-xs"
                >
                    <PlusIcon className="w-4 h-4" /> Add Experience
                </button>
            </div>

            {/* Exp Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {experiences.map(exp => (
                    <div
                        key={exp.key}
                        onClick={() => handleEditExperience(exp.key)}
                        className="group relative p-6 bg-white dark:bg-slate-800 rounded-3xl shadow-sm border border-slate-200 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-400 transition-all cursor-pointer flex flex-col h-full"
                    >
                        <div className="flex justify-between items-start mb-6">
                            <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-2xl group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 transition-colors">
                                <BuildingOfficeIcon className="w-6 h-6 text-slate-400 group-hover:text-blue-500" />
                            </div>
                            <div className="flex flex-col items-end gap-2">
                                <span className="flex items-center gap-1.5 text-[10px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest bg-blue-50 dark:bg-blue-900/20 px-3 py-1 rounded-full border border-blue-100 dark:border-blue-900/30">
                                    <CheckBadgeIcon className="w-3.5 h-3.5" /> Active Formula
                                </span>
                                <button
                                    onClick={(e) => handleDeleteExperience(e, exp.key)}
                                    className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-300 hover:text-red-500 rounded-xl transition-all"
                                    title="Delete Experience"
                                >
                                    <TrashIcon className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        <div className="mb-4">
                            <h3 className="font-extrabold text-slate-900 dark:text-white text-xl mb-1 tracking-tight truncate">
                                {exp.latest.metadata?.company as string}
                            </h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400 font-bold italic truncate">
                                {exp.latest.metadata?.role_title as string}
                            </p>
                        </div>

                        <div className="space-y-4 mb-6">
                            <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                                <CalendarIcon className="w-4 h-4 opacity-50" />
                                {exp.latest.metadata?.start_date ? new Date(exp.latest.metadata.start_date as string).toLocaleDateString() : 'N/A'} - {exp.latest.metadata?.is_current ? 'Present' : (exp.latest.metadata?.end_date ? new Date(exp.latest.metadata.end_date as string).toLocaleDateString() : 'N/A')}
                            </div>
                            <div className="p-4 bg-slate-50 dark:bg-slate-900/40 rounded-2xl border border-slate-100 dark:border-slate-800/50">
                                <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-3 font-mono leading-relaxed italic">
                                    "{exp.latest.content_snippet?.substring(0, 150) || 'No narrative content available'}..."
                                </p>
                            </div>
                        </div>

                        <div className="mt-auto pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-[10px] text-slate-400 font-black uppercase tracking-widest">
                            <span className="flex items-center gap-1.5">
                                <ClockIcon className="w-3.5 h-3.5" /> v{exp.versions.length} Synchronization
                            </span>
                            <span className="flex items-center text-blue-600 dark:text-blue-400 font-black group-hover:translate-x-1 transition-transform">
                                Edit <ChevronRightIcon className="w-3.5 h-3.5 ml-0.5" />
                            </span>
                        </div>
                    </div>
                ))}

                {experiences.length === 0 && (
                    <div
                        onClick={handleAddNew}
                        className="p-12 border-4 border-dashed border-slate-100 dark:border-slate-800/50 rounded-[3rem] flex flex-col items-center justify-center text-center group hover:border-blue-200 dark:hover:border-blue-900/30 transition-all cursor-pointer bg-slate-50/30 dark:bg-slate-900/10"
                    >
                        <div className="p-5 bg-white dark:bg-slate-800 rounded-3xl shadow-sm mb-6 group-hover:scale-110 transition-transform">
                            <PlusIcon className="w-10 h-10 text-slate-300 group-hover:text-blue-500" />
                        </div>
                        <h4 className="text-lg font-black text-slate-900 dark:text-white uppercase tracking-tight mb-2">Initialize Job History</h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium max-w-[200px] leading-relaxed">
                            Start adding your career experiences to build your vector formula library.
                        </p>
                    </div>
                )}
            </div>

            {/* Editor Overlay */}
            {selectedExpKey && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-xl animate-fade-in overflow-y-auto">
                    <div className="bg-white dark:bg-slate-900 w-full max-w-5xl rounded-[3rem] shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col max-h-[95vh] my-4">
                        <div className="p-8 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/60 backdrop-blur-sm sticky top-0 z-10">
                            <div className="flex items-center gap-5">
                                <div className="p-4 bg-blue-600 rounded-[1.5rem] shadow-xl shadow-blue-500/30">
                                    <SparklesIcon className="w-7 h-7 text-white" />
                                </div>
                                <div className="space-y-1">
                                    <h3 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase">
                                        {selectedExpKey === 'new' ? 'New Career Experience' : 'Formula Refinement'}
                                    </h3>
                                    <p className="text-xs text-slate-500 dark:text-slate-400 font-bold tracking-wide italic">
                                        Aligning high-fidelity proof points with metadata vectors.
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedExpKey(null)}
                                className="p-4 hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-400 hover:text-red-500 rounded-2xl transition-all group"
                            >
                                <span className="text-2xl transition-transform group-hover:rotate-90">✕</span>
                            </button>
                        </div>

                        <div className="p-10 lg:p-14 space-y-12 overflow-y-auto custom-scrollbar flex-1">
                            {/* Form Sections */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10">
                                {/* Left Column: Core Identity */}
                                <div className="space-y-10">
                                    <div className="space-y-4">
                                        <label className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">
                                            <BuildingOfficeIcon className="w-3 h-3" /> Core Company Details
                                        </label>
                                        <div className="space-y-6">
                                            <div className="relative">
                                                <input
                                                    placeholder="Company Name"
                                                    value={formData.company}
                                                    onChange={e => setFormData({ ...formData, company: e.target.value })}
                                                    className={`w-full p-5 bg-slate-50 dark:bg-slate-950/50 border ${errors.company ? 'border-red-500' : 'border-slate-200 dark:border-slate-800'} rounded-2xl focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 outline-none transition-all font-bold text-slate-900 dark:text-white`}
                                                />
                                                {errors.company && <p className="absolute -bottom-5 left-1 text-[9px] font-black text-red-500 uppercase">{errors.company}</p>}
                                            </div>
                                            <div className="relative">
                                                <input
                                                    placeholder="Role Title"
                                                    value={formData.role}
                                                    onChange={e => setFormData({ ...formData, role: e.target.value })}
                                                    className={`w-full p-5 bg-slate-50 dark:bg-slate-950/50 border ${errors.role ? 'border-red-500' : 'border-slate-200 dark:border-slate-800'} rounded-2xl focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 outline-none transition-all font-bold text-slate-900 dark:text-white`}
                                                />
                                                {errors.role && <p className="absolute -bottom-5 left-1 text-[9px] font-black text-red-500 uppercase">{errors.role}</p>}
                                            </div>
                                            <div className="relative">
                                                <input
                                                    placeholder="Location (City, State / Remote)"
                                                    value={formData.location}
                                                    onChange={e => setFormData({ ...formData, location: e.target.value })}
                                                    className="w-full p-5 bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 outline-none transition-all font-bold text-slate-900 dark:text-white"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <label className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">
                                            <CalendarIcon className="w-3 h-3" /> Duration & Timeline
                                        </label>
                                        <div className="grid grid-cols-2 gap-5">
                                            <div className="relative">
                                                <label className="block text-[8px] font-black text-slate-400 uppercase mb-1 ml-1">Start Date</label>
                                                <input
                                                    type="date"
                                                    value={formData.startDate}
                                                    onChange={e => setFormData({ ...formData, startDate: e.target.value })}
                                                    className={`w-full p-4 bg-slate-50 dark:bg-slate-950/50 border ${errors.startDate ? 'border-red-500' : 'border-slate-200 dark:border-slate-800'} rounded-2xl focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 outline-none transition-all font-bold text-slate-900 dark:text-white text-sm`}
                                                />
                                            </div>
                                            <div className="relative">
                                                <div className="flex items-center justify-between mb-1">
                                                    <label className="block text-[8px] font-black text-slate-400 uppercase ml-1">End Date</label>
                                                    <label className="flex items-center gap-1.5 cursor-pointer group">
                                                        <input
                                                            type="checkbox"
                                                            checked={formData.isCurrent}
                                                            onChange={e => setFormData({ ...formData, isCurrent: e.target.checked, endDate: e.target.checked ? '' : formData.endDate })}
                                                            className="w-3 h-3 rounded text-blue-600 focus:ring-blue-500 border-slate-300"
                                                        />
                                                        <span className="text-[9px] font-black text-slate-500 uppercase group-hover:text-blue-500 transition-colors">Current</span>
                                                    </label>
                                                </div>
                                                <input
                                                    type="date"
                                                    disabled={formData.isCurrent}
                                                    value={formData.endDate}
                                                    onChange={e => setFormData({ ...formData, endDate: e.target.value })}
                                                    className={`w-full p-4 bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 outline-none transition-all font-bold text-slate-900 dark:text-white text-sm disabled:opacity-40 disabled:cursor-not-allowed`}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Right Column: Metadata Vectors */}
                                <div className="space-y-10">
                                    <div className="space-y-4">
                                        <label className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">
                                            <TagIcon className="w-3 h-3" /> Impact & Skill Vectors
                                        </label>
                                        <div className="space-y-8">
                                            <div className="space-y-2">
                                                <label className="block text-[9px] font-black text-slate-500 uppercase ml-1 italic">Core Impact Skills (Comma separated)</label>
                                                <input
                                                    placeholder="Product Strategy, GTM, System Architecture..."
                                                    value={formData.skills}
                                                    onChange={e => setFormData({ ...formData, skills: e.target.value })}
                                                    className="w-full p-4 bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 outline-none transition-all font-bold text-slate-900 dark:text-white text-sm"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="block text-[9px] font-black text-slate-500 uppercase ml-1 italic">Tactical Keywords</label>
                                                <input
                                                    placeholder="B2B SAS, Microservices, Kubernetes, SEO..."
                                                    value={formData.keywords}
                                                    onChange={e => setFormData({ ...formData, keywords: e.target.value })}
                                                    className="w-full p-4 bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 outline-none transition-all font-bold text-slate-900 dark:text-white text-sm"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="block text-[9px] font-black text-slate-500 uppercase ml-1 italic">Technical Architecture (Optional)</label>
                                                <input
                                                    placeholder="Distributed Systems, Snowflake, React Native..."
                                                    value={formData.architecture}
                                                    onChange={e => setFormData({ ...formData, architecture: e.target.value })}
                                                    className="w-full p-4 bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 outline-none transition-all font-bold text-slate-900 dark:text-white text-sm"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Full Experience Narrative Editor */}
                            <div className="space-y-8">
                                <div className="flex items-center justify-between ml-1">
                                    <label className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                                        <DocumentTextIcon className="w-3 h-3" /> Experience Formula (Master Narrative)
                                    </label>
                                    <div className="flex items-center gap-6">
                                        <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                            <div className="w-1.5 h-1.5 rounded-full bg-green-500" /> Vectorizable Content
                                        </div>
                                    </div>
                                </div>
                                <div className="relative group">
                                    <textarea
                                        value={formData.content}
                                        onChange={e => setFormData({ ...formData, content: e.target.value })}
                                        rows={12}
                                        className={`w-full p-10 bg-slate-50 dark:bg-slate-950 border ${errors.content ? 'border-red-500' : 'border-slate-200 dark:border-slate-800'} rounded-[3rem] focus:ring-8 focus:ring-blue-500/5 focus:border-blue-500 transition-all outline-none font-mono text-base text-slate-800 dark:text-slate-200 placeholder:text-slate-300 dark:placeholder:text-slate-800 leading-relaxed shadow-inner`}
                                        placeholder="Articulate the core challenges, specific actions, and quantifiable results for this role..."
                                    />
                                    {errors.content && <p className="absolute -bottom-6 left-1 text-[10px] font-black text-red-500 uppercase italic">Error: Detailed content required for AI matching</p>}

                                    <div className="absolute right-10 bottom-10 opacity-0 group-focus-within:opacity-100 transition-all transform translate-y-2 group-focus-within:translate-y-0">
                                        <span className="px-4 py-2 bg-blue-600 text-[10px] font-black text-white rounded-xl uppercase tracking-widest shadow-lg shadow-blue-500/40 flex items-center gap-2">
                                            <BoltIcon className="w-3 h-3" /> Formula Engine Active
                                        </span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-8 p-10 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10 rounded-[3rem] border border-blue-100/50 dark:border-blue-900/30">
                                    <div className="p-4 bg-white dark:bg-slate-800 rounded-3xl shadow-lg shadow-blue-500/10">
                                        <SparklesIcon className="w-10 h-10 text-blue-500 animate-pulse" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-tight mb-2 flex items-center gap-2">
                                            Deep Vector Alignment <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-[8px] text-blue-600 dark:text-blue-400 rounded-md">Metadata Injected</span>
                                        </p>
                                        <p className="text-xs text-slate-600 dark:text-slate-400 font-semibold leading-relaxed">
                                            By structuring this experience with specific metadata (skills, keywords, architecture), you allow the AI matching engine to perform high-fidelity comparisons against job requirements. This content becomes the single "Active Proof Point" for this career chapter.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-10 bg-slate-50/50 dark:bg-slate-900/60 backdrop-blur-md border-t border-slate-100 dark:border-slate-800 flex justify-end gap-6 sticky bottom-0 z-10">
                            <button
                                onClick={() => setSelectedExpKey(null)}
                                className="px-10 py-4 text-xs font-black text-slate-500 dark:text-slate-500 hover:text-slate-900 dark:hover:text-white transition-all uppercase tracking-widest"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="px-14 py-4 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white text-xs font-black rounded-2xl shadow-2xl shadow-blue-500/30 disabled:opacity-50 disabled:shadow-none transition-all flex items-center gap-4 uppercase tracking-widest"
                            >
                                {isSaving ? <LoadingSpinner className="w-4 h-4" /> : (
                                    <>
                                        <BoltIcon className="w-4 h-4" /> Sync Formula
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

import React, { useState, useEffect, useCallback } from 'react';
import {
    StrategicNarrative,
    CareerBrandSection,
    CAREER_BRAND_SECTIONS,
    DocumentDetail,
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
    RocketLaunchIcon,
    ArrowTrendingUpIcon,
    CurrencyDollarIcon,
    ClipboardDocumentListIcon,
    GlobeAltIcon,
} from './IconComponents';

interface CareerBrandDashboardProps {
    activeNarrative: StrategicNarrative;
    onUpdateNarrative: (narrative: StrategicNarrative) => void;
}

const getSectionIcon = (sectionId: CareerBrandSection) => {
    switch (sectionId) {
        case 'full_document': return ClipboardDocumentListIcon;
        case 'north_star': return RocketLaunchIcon;
        case 'trajectory_mastery': return ArrowTrendingUpIcon;
        case 'values_compass': return CheckBadgeIcon;
        case 'purpose_impact': return SparklesIcon;
        case 'lifestyle_alignment': return ClockIcon;
        case 'compensation_philosophy': return CurrencyDollarIcon;
        case 'career_story': return ClipboardDocumentListIcon;
        case 'narratives_proof_points': return DocumentTextIcon;
        default: return DocumentTextIcon;
    }
};

const DimensionCard = ({
    section,
    doc,
    onClick
}: any) => {
    const hasContent = !!doc && doc.content.length > 0;
    const Icon = getSectionIcon(section.id);

    return (
        <div
            onClick={onClick}
            className={`group relative p-5 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-400 transition-all cursor-pointer flex flex-col h-full ${section.id === 'full_document' ? 'md:col-span-2 lg:col-span-3 bg-blue-50/30' : ''}`}
        >
            <div className="flex justify-between items-start mb-3">
                <div className="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 transition-colors">
                    <Icon className="w-5 h-5 text-slate-400 group-hover:text-blue-500" />
                </div>
                {doc?.metadata?.is_latest && (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-green-600 dark:text-green-400 uppercase tracking-wider bg-green-50 dark:bg-green-900/20 px-2 py-0.5 rounded-full">
                        <CheckBadgeIcon className="w-3 h-3" /> Latest
                    </span>
                )}
            </div>

            <h3 className="font-bold text-slate-800 dark:text-slate-100 text-lg mb-1">{section.name}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 line-clamp-2">{section.description}</p>

            <div className="mt-auto">
                {hasContent ? (
                    <div className="space-y-3">
                        <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-100 dark:border-slate-800">
                            <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-3 italic">
                                "{doc.content.substring(0, 150)}..."
                            </p>
                        </div>
                        <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase tracking-tighter font-semibold">
                            <span className="flex items-center gap-1">
                                <ClockIcon className="w-3 h-3" /> v{Number(doc.metadata?.version) || 1} • {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Unknown'}
                            </span>
                            <span className="flex items-center text-blue-500 font-bold group-hover:translate-x-1 transition-transform">
                                Edit <ChevronRightIcon className="w-3 h-3 ml-0.5" />
                            </span>
                        </div>
                    </div>
                ) : (
                    <div className="flex items-center justify-center p-6 border-2 border-dashed border-slate-100 dark:border-slate-800 rounded-lg group-hover:border-blue-200 dark:group-hover:border-blue-900/50 transition-colors">
                        <div className="text-center">
                            <PlusIcon className="w-6 h-6 text-slate-300 mx-auto mb-2" />
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Define Section</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export const CareerBrandDashboard = ({ activeNarrative, onUpdateNarrative }: CareerBrandDashboardProps) => {
    const [docs, setDocs] = useState<Partial<Record<CareerBrandSection, DocumentDetail | null>>>({});
    const [isLoading, setIsLoading] = useState(true);
    const [selectedSection, setSelectedSection] = useState<CareerBrandSection | null>(null);
    const [editContent, setEditContent] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    const { addToast } = useToast();

    const fetchDocs = useCallback(async () => {
        if (!activeNarrative.narrative_id) return;
        setIsLoading(true);
        try {
            const results = await Promise.all(
                CAREER_BRAND_SECTIONS.map(async (section) => {
                    try {
                        let detail = await apiService.getLatestDocumentByDimension(section.id);

                        // Fallback for north_star rename
                        if ((!detail || detail.id === 'unknown') && section.id === 'north_star') {
                            const fallbackDetail = await apiService.getLatestDocumentByDimension('north_star_vision' as any);
                            if (fallbackDetail && fallbackDetail.id !== 'unknown') {
                                detail = fallbackDetail;
                            }
                        }

                        return { id: section.id, detail: (detail && detail.id !== 'unknown') ? detail : null };
                    } catch (e) {
                        return { id: section.id, detail: null };
                    }
                })
            );

            const newDocs: Partial<Record<CareerBrandSection, DocumentDetail | null>> = {};
            results.forEach(res => {
                newDocs[res.id as CareerBrandSection] = res.detail;
            });
            setDocs(newDocs);
        } finally {
            setIsLoading(false);
        }
    }, [activeNarrative.narrative_id]);

    useEffect(() => {
        fetchDocs();
    }, [fetchDocs]);

    const handleSaveSection = async () => {
        if (!selectedSection || !activeNarrative.narrative_id) return;

        setIsSaving(true);
        try {
            const sectionInfo = CAREER_BRAND_SECTIONS.find(s => s.id === selectedSection);
            await apiService.uploadCareerBrand({
                profile_id: activeNarrative.narrative_id,
                section: selectedSection,
                title: sectionInfo?.name || selectedSection,
                content: editContent
            });

            addToast(`${sectionInfo?.name} updated successfully`, 'success');
            await fetchDocs();
            setSelectedSection(null);
        } catch (error) {
            addToast('Failed to save section', 'error');
        } finally {
            setIsSaving(false);
        }
    };

    useEffect(() => {
        if (selectedSection) {
            setEditContent(docs[selectedSection]?.content || '');
        }
    }, [selectedSection, docs]);

    if (isLoading && Object.keys(docs).length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 animate-pulse">
                <LoadingSpinner />
                <p className="mt-4 text-slate-500 font-medium tracking-tight">Loading your brand framework...</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Dimensions Grid */}
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Career Brand Dimensions</h2>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Manage the {CAREER_BRAND_SECTIONS.length} core pillars of your professional identity in the knowledge base.</p>
                    </div>
                    <div className="flex gap-2">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs font-bold text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                            <div className="w-2 h-2 rounded-full bg-blue-500" /> ChromaDB Synced
                        </span>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {CAREER_BRAND_SECTIONS.map(section => (
                        <DimensionCard
                            key={section.id}
                            section={section}
                            doc={docs[section.id] || null}
                            onClick={() => setSelectedSection(section.id)}
                        />
                    ))}
                </div>
            </div>

            {/* Editor Modal */}
            {selectedSection && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
                    <div className="bg-white dark:bg-slate-800 w-full max-w-3xl rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden flex flex-col max-h-[90vh]">
                        <div className="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-900/40">
                            <div>
                                <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
                                    Define {CAREER_BRAND_SECTIONS.find(s => s.id === selectedSection)?.name}
                                </h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium italic">
                                    {CAREER_BRAND_SECTIONS.find(s => s.id === selectedSection)?.description}
                                </p>
                            </div>
                            <button
                                onClick={() => setSelectedSection(null)}
                                className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-full transition-colors"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="p-8 space-y-6 overflow-y-auto">
                            <div className="relative group">
                                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">Content</label>
                                <textarea
                                    value={editContent}
                                    onChange={e => setEditContent(e.target.value)}
                                    rows={12}
                                    className="w-full p-5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none font-sans text-lg text-slate-800 dark:text-slate-100 placeholder:text-slate-300 dark:placeholder:text-slate-700 leading-relaxed"
                                    placeholder="Enter your brand narrative here..."
                                />
                                <div className="absolute right-4 bottom-4 opacity-0 group-focus-within:opacity-100 transition-opacity">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Self-Reflect & Articulate</span>
                                </div>
                            </div>

                            <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-100 dark:border-blue-900/30">
                                <SparklesIcon className="w-6 h-6 text-blue-500" />
                                <div className="flex-1">
                                    <p className="text-xs font-bold text-blue-800 dark:text-blue-300">Need inspiration?</p>
                                    <p className="text-[10px] text-blue-600/70 dark:text-blue-400/70">Reflect on your most impactful achievements and core values. Be specific and authentic.</p>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 bg-slate-50 dark:bg-slate-900/40 border-t border-slate-100 dark:border-slate-700 flex justify-end gap-3">
                            <button
                                onClick={() => setSelectedSection(null)}
                                className="px-6 py-2.5 text-sm font-bold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveSection}
                                disabled={isSaving || !editContent.trim()}
                                className="px-8 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-black rounded-xl shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:shadow-none transition-all flex items-center gap-2"
                            >
                                {isSaving ? <LoadingSpinner /> : 'Sync to Knowledge Base'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

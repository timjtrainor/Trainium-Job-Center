import React from 'react';
import { CompanyInfoResult, KeywordsResult, GuidanceResult } from '../types';
import { MarkdownPreview } from './MarkdownPreview';

interface GuidanceModalProps {
    isOpen: boolean;
    onClose: () => void;
    companyInfo: CompanyInfoResult;
    aiSummary: string;
    keywords: KeywordsResult | null;
    guidance: GuidanceResult | null;
}

const Section = ({ title, children }: { title: string, children: React.ReactNode }) => (
    <div className="py-4 border-b border-slate-200 dark:border-slate-700 last:border-b-0">
        <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">{title}</h3>
        <div className="text-sm text-slate-600 dark:text-slate-300 space-y-2">{children}</div>
    </div>
);

export const GuidanceModal = ({ isOpen, onClose, companyInfo, aiSummary, keywords, guidance }: GuidanceModalProps): React.ReactNode => {
    if (!isOpen) {
        return null;
    }

    return (
        <div className="relative z-50" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-xl font-bold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                AI Strategic Guidance
                            </h3>
                            <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-4">
                               <Section title="Company Intelligence">
                                    <p><strong>Mission:</strong> {companyInfo.mission?.text || 'N/A'}</p>
                                    <p><strong>Values:</strong> {companyInfo.values?.text || 'N/A'}</p>
                                    <p><strong>Goals:</strong> {companyInfo.goals?.text || 'N/A'}</p>
                                    <p><strong>Issues:</strong> {companyInfo.issues?.text || 'N/A'}</p>
                                    <p><strong>Customer Segments:</strong> {companyInfo.customer_segments?.text || 'N/A'}</p>
                                    <p><strong>Strategic Initiatives:</strong> {companyInfo.strategic_initiatives?.text || 'N/A'}</p>
                                    <p><strong>Market Position:</strong> {companyInfo.market_position?.text || 'N/A'}</p>
                                    <p><strong>Recent News:</strong> {companyInfo.news?.text || 'N/A'}</p>
                                </Section>
                                <Section title="Job Problem Analysis">
                                    <MarkdownPreview markdown={aiSummary} />
                                </Section>
                                <Section title="Keywords">
                                    <p><strong>Hard Skills:</strong> {keywords?.hard_keywords.map(k => k.keyword).join(', ') || 'N/A'}</p>
                                    <p><strong>Soft Skills:</strong> {keywords?.soft_keywords.map(k => k.keyword).join(', ') || 'N/A'}</p>
                                </Section>
                                <Section title="Resume Guidance">
                                    <p><strong>Summary Guidance:</strong> {guidance?.summary.join(' ') || 'N/A'}</p>
                                    <p><strong>Bullet Guidance:</strong> {guidance?.bullets.join(' ') || 'N/A'}</p>
                                    <p><strong>Key Themes:</strong> {guidance?.keys.join(', ') || 'N/A'}</p>
                                </Section>
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            <button type="button" onClick={onClose} className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
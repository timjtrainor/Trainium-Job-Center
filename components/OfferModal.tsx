import React, { useState, useEffect } from 'react';
import { Offer, OfferPayload, Prompt, StrategicNarrative, JobProblemAnalysisResult, PromptContext } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, SparklesIcon } from './IconComponents';

interface OfferModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (offerData: OfferPayload, offerId?: string) => Promise<void>;
    offer: Partial<Offer> | null;
    prompts: Prompt[];
    activeNarrative: StrategicNarrative | null;
    jobProblemAnalysis: JobProblemAnalysisResult | null;
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}

export const OfferModal = ({ isOpen, onClose, onSave, offer, prompts, activeNarrative, jobProblemAnalysis, debugCallbacks }: OfferModalProps) => {
    const [editableOffer, setEditableOffer] = useState<Partial<Offer>>(offer || {});
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [isGenerating, setIsGenerating] = useState(false);
    const [negotiationGoal, setNegotiationGoal] = useState('');
    const [negotiationScript, setNegotiationScript] = useState<{ talking_points: string[], email_draft: string } | null>(null);

    useEffect(() => {
        if (isOpen) {
            setEditableOffer(offer || {});
            setError(null);
            setIsLoading(false);
            setNegotiationScript(null);
            setNegotiationGoal('');
        }
    }, [isOpen, offer]);

    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setEditableOffer(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        try {
            const { offer_id, created_at, user_id, ...payload } = editableOffer;
            await onSave(payload as OfferPayload, offer_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save offer.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateScript = async () => {
        if (!activeNarrative) {
            setError("Active narrative is required to generate a negotiation script.");
            return;
        }
        setIsGenerating(true);
        setError(null);
        try {
            const prompt = prompts.find(p => p.id === 'GENERATE_NEGOTIATION_SCRIPT');
            if (!prompt) throw new Error("Negotiation script prompt not found.");

            const context: PromptContext = {
                STRATEGIC_NARRATIVE: JSON.stringify(activeNarrative),
                CORE_PROBLEM_ANALYSIS: jobProblemAnalysis?.core_problem_analysis.core_problem,
                OFFER_DETAILS: JSON.stringify(editableOffer),
                NEGOTIATION_GOAL: negotiationGoal || 'Improve the overall package, focusing on base salary.',
            };

            const result = await geminiService.generateNegotiationScript(context, prompt.content, debugCallbacks);
            setNegotiationScript(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to generate script.");
        } finally {
            setIsGenerating(false);
        }
    };
    
    const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
    const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl">
                        <form onSubmit={handleSubmit}>
                            <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                                <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                    {offer?.offer_id ? 'Edit Offer Details' : 'Log Offer Details'}
                                </h3>
                                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6 max-h-[75vh] overflow-y-auto pr-2">
                                    {/* Left: Offer Form */}
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            <div><label htmlFor="company_name" className={labelClass}>Company</label><input type="text" id="company_name" name="company_name" value={editableOffer.company_name || ''} onChange={handleChange} className={inputClass} disabled /></div>
                                            <div><label htmlFor="job_title" className={labelClass}>Job Title</label><input type="text" id="job_title" name="job_title" value={editableOffer.job_title || ''} onChange={handleChange} className={inputClass} disabled /></div>
                                        </div>
                                        <div><label htmlFor="base_salary" className={labelClass}>Base Salary</label><input type="number" id="base_salary" name="base_salary" value={editableOffer.base_salary || ''} onChange={handleChange} className={inputClass} placeholder="e.g., 180000" /></div>
                                        <div><label htmlFor="bonus_potential" className={labelClass}>Bonus</label><input type="text" id="bonus_potential" name="bonus_potential" value={editableOffer.bonus_potential || ''} onChange={handleChange} className={inputClass} placeholder="e.g., 20% target" /></div>
                                        <div><label htmlFor="equity_details" className={labelClass}>Equity</label><input type="text" id="equity_details" name="equity_details" value={editableOffer.equity_details || ''} onChange={handleChange} className={inputClass} placeholder="e.g., 10,000 RSUs over 4 years" /></div>
                                        <div><label htmlFor="benefits_summary" className={labelClass}>Benefits Summary</label><textarea id="benefits_summary" name="benefits_summary" value={editableOffer.benefits_summary || ''} onChange={handleChange} rows={3} className={inputClass} placeholder="e.g., Medical, Dental, 401k match" /></div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            <div><label htmlFor="deadline" className={labelClass}>Response Deadline</label><input type="date" id="deadline" name="deadline" value={editableOffer.deadline || ''} onChange={handleChange} className={inputClass} /></div>
                                            <div><label htmlFor="status" className={labelClass}>Status</label><select id="status" name="status" value={editableOffer.status || 'Received'} onChange={handleChange} className={inputClass}><option>Received</option><option>Negotiating</option><option>Accepted</option><option>Declined</option></select></div>
                                        </div>
                                    </div>

                                    {/* Right: AI Coach */}
                                    <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg space-y-3 border border-slate-200 dark:border-slate-700">
                                        <h4 className="font-semibold text-slate-800 dark:text-slate-200">AI Negotiation Coach</h4>
                                        <div>
                                            <label htmlFor="negotiation_goal" className="text-sm font-medium text-slate-600 dark:text-slate-400">What's your primary goal?</label>
                                            <input type="text" id="negotiation_goal" value={negotiationGoal} onChange={e => setNegotiationGoal(e.target.value)} className={`${inputClass} mt-1`} placeholder="e.g., Increase base by 10%" />
                                        </div>
                                        <button type="button" onClick={handleGenerateScript} disabled={isGenerating} className="inline-flex w-full justify-center items-center gap-2 px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400">
                                            {isGenerating ? <LoadingSpinner/> : <SparklesIcon className="h-4 w-4" />} Generate Script
                                        </button>
                                        {negotiationScript && (
                                            <div className="space-y-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                                                <div>
                                                    <h5 className="text-sm font-semibold">Talking Points</h5>
                                                    <ul className="list-disc pl-5 text-xs space-y-1 mt-1">
                                                        {negotiationScript.talking_points.map((p, i) => <li key={i}>{p}</li>)}
                                                    </ul>
                                                </div>
                                                <div>
                                                    <h5 className="text-sm font-semibold">Email Draft</h5>
                                                    <textarea readOnly rows={8} value={negotiationScript.email_draft.replace(/\\n/g, '\n')} className={`${inputClass} mt-1 text-xs`}></textarea>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
                            </div>
                            <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                                <button type="submit" disabled={isLoading} className="inline-flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-700 sm:ml-3 sm:w-auto disabled:opacity-50">
                                    {isLoading ? <LoadingSpinner /> : 'Save Offer'}
                                </button>
                                <button type="button" onClick={onClose} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};
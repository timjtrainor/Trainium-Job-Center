import React, { useState, useEffect } from 'react';
import { CompanyPayload, Prompt, PromptContext, InfoField, Company } from '../types';
import { LoadingSpinner } from './IconComponents';
import * as geminiService from '../services/geminiService';

interface CreateCompanyModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (companyData: CompanyPayload) => Promise<Company>;
    initialData?: Partial<CompanyPayload> | null;
    prompts: Prompt[];
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}

const emptyInfoField: InfoField = { text: '', source: '' };

const initialFormState: CompanyPayload = {
    company_name: '',
    company_url: '',
    is_recruiting_firm: false,
    mission: emptyInfoField,
    values: emptyInfoField,
    news: emptyInfoField,
    goals: emptyInfoField,
    issues: emptyInfoField,
    customer_segments: emptyInfoField,
    strategic_initiatives: emptyInfoField,
    market_position: emptyInfoField,
    competitors: emptyInfoField,
    industry: emptyInfoField,
};

const InfoFieldEditor = ({
    label,
    field,
    onChange,
    rows = 3
}: {
    label: string,
    field: InfoField,
    onChange: (newText: string) => void
    rows?: number,
}) => (
    <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">{label}</label>
        <textarea
            rows={rows}
            value={field?.text || ''}
            onChange={(e) => onChange(e.target.value)}
            className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm font-sans"
        />
        {field?.source && (
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Source: <a href={field.source} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline truncate inline-block max-w-full align-bottom">{field.source}</a>
            </div>
        )}
    </div>
);


export const CreateCompanyModal = ({ isOpen, onClose, onCreate, initialData, prompts, debugCallbacks }: CreateCompanyModalProps): React.ReactNode => {

    const [companyData, setCompanyData] = useState<CompanyPayload>(initialFormState);
    const [isLoading, setIsLoading] = useState(false);
    const [isResearching, setIsResearching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            // Reset form when modal opens, applying initial data if provided
            setCompanyData({ ...initialFormState, ...(initialData || {}) });
            setError(null);
            setIsLoading(false);
            setIsResearching(false);
        }
    }, [isOpen, initialData]);

    if (!isOpen) {
        return null;
    }

    const handleSimpleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value, type, checked } = e.target;
        if (type === 'checkbox') {
            setCompanyData(prev => ({ ...prev, [name]: checked }));
        } else {
            setCompanyData(prev => ({ ...prev, [name]: value }));
        }
    };

    const handleInfoChange = (fieldName: keyof CompanyPayload, newText: string) => {
        setCompanyData(prev => ({
            ...prev,
            [fieldName]: {
                ...((prev[fieldName as keyof CompanyPayload] as InfoField) || { text: '', source: '' }),
                text: newText
            }
        }));
    };


    const handleResearch = async () => {
        if (!companyData.company_name?.trim()) {
            setError('Please enter a company name before researching.');
            return;
        }
        setIsResearching(true);
        setError(null);
        try {
            const prompt = prompts.find(p => p.id === 'COMPANY_GOAL_ANALYSIS');
            if (!prompt) throw new Error("Company research prompt not found.");

            const context: PromptContext = {
                COMPANY_NAME: companyData.company_name,
                COMPANY_HOMEPAGE: companyData.company_url
            };

            const info = await geminiService.researchCompanyInfo(context, prompt.id, debugCallbacks);

            setCompanyData(prev => ({
                ...prev,
                mission: info.mission.text ? info.mission : prev.mission,
                values: info.values.text ? info.values : prev.values,
                news: info.news.text ? info.news : prev.news,
                goals: info.goals.text ? info.goals : prev.goals,
                issues: info.issues.text ? info.issues : prev.issues,
                customer_segments: info.customer_segments.text ? info.customer_segments : prev.customer_segments,
                strategic_initiatives: info.strategic_initiatives.text ? info.strategic_initiatives : prev.strategic_initiatives,
                market_position: info.market_position.text ? info.market_position : prev.market_position,
                industry: info.industry.text ? info.industry : prev.industry,
                competitors: info.competitors.text ? info.competitors : prev.competitors,
            }));

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to research company.');
        } finally {
            setIsResearching(false);
        }
    };


    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!companyData.company_name?.trim()) {
            setError('Company name is required.');
            return;
        }
        setIsLoading(true);
        setError(null);
        try {
            await onCreate(companyData);
            // Parent component (App.tsx) is responsible for closing the modal
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save company. Please try again.');
            setIsLoading(false); // Stop loading on error so user can retry
        }
    };

    const inputClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
    const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>

            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl">
                        <form onSubmit={handleSubmit}>
                            <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                                <div className="sm:flex sm:items-start">
                                    <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                                        <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                            Create New Company
                                        </h3>
                                        <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-2">
                                            {error && (
                                                <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
                                                    <p className="text-sm font-medium text-red-800 dark:text-red-300">{error}</p>
                                                </div>
                                            )}

                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                                <div className="sm:col-span-2">
                                                    <label htmlFor="company_name" className={labelClass}>
                                                        Company Name <span className="text-red-500">*</span>
                                                    </label>
                                                    <input type="text" name="company_name" id="company_name" value={companyData.company_name} onChange={handleSimpleChange} className={inputClass} required disabled={isLoading || isResearching} />
                                                </div>
                                                <div className="sm:col-span-2">
                                                    <label htmlFor="company_url" className={labelClass}>
                                                        Company URL (for AI research)
                                                    </label>
                                                    <input type="url" name="company_url" id="company_url" value={companyData.company_url || ''} onChange={handleSimpleChange} className={inputClass} placeholder="https://www.company.com" disabled={isLoading || isResearching} />
                                                </div>
                                                <div className="sm:col-span-2 flex items-center gap-2">
                                                    <input
                                                        type="checkbox"
                                                        name="is_recruiting_firm"
                                                        id="is_recruiting_firm"
                                                        checked={!!companyData.is_recruiting_firm}
                                                        onChange={handleSimpleChange}
                                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                        disabled={isLoading || isResearching}
                                                    />
                                                    <label htmlFor="is_recruiting_firm" className={labelClass}>
                                                        This is a recruiting firm
                                                    </label>
                                                </div>
                                            </div>

                                            <div className="py-2 text-center">
                                                <button
                                                    type="button"
                                                    onClick={handleResearch}
                                                    disabled={isResearching || isLoading || !companyData.company_name?.trim()}
                                                    className="inline-flex items-center justify-center w-full sm:w-auto px-4 py-2 text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed"
                                                >
                                                    {isResearching ? <LoadingSpinner /> : 'Research Company with AI'}
                                                </button>
                                            </div>

                                            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                                                <InfoFieldEditor label="Mission" field={companyData.mission || emptyInfoField} onChange={(text) => handleInfoChange('mission', text)} rows={3} />
                                                <InfoFieldEditor label="Values" field={companyData.values || emptyInfoField} onChange={(text) => handleInfoChange('values', text)} rows={3} />
                                                <InfoFieldEditor label="Goals" field={companyData.goals || emptyInfoField} onChange={(text) => handleInfoChange('goals', text)} rows={3} />
                                                <InfoFieldEditor label="Challenges / Issues" field={companyData.issues || emptyInfoField} onChange={(text) => handleInfoChange('issues', text)} rows={3} />
                                                <InfoFieldEditor label="Customer Segments" field={companyData.customer_segments || emptyInfoField} onChange={(text) => handleInfoChange('customer_segments', text)} rows={3} />
                                                <InfoFieldEditor label="Strategic Initiatives" field={companyData.strategic_initiatives || emptyInfoField} onChange={(text) => handleInfoChange('strategic_initiatives', text)} rows={3} />
                                                <div className="sm:col-span-2"><InfoFieldEditor label="Market Position" field={companyData.market_position || emptyInfoField} onChange={(text) => handleInfoChange('market_position', text)} rows={2} /></div>
                                                <div className="sm:col-span-2"><InfoFieldEditor label="Recent News" field={companyData.news || emptyInfoField} onChange={(text) => handleInfoChange('news', text)} rows={2} /></div>
                                                <div className="sm:col-span-2"><InfoFieldEditor label="Industry" field={companyData.industry || emptyInfoField} onChange={(text) => handleInfoChange('industry', text)} rows={1} /></div>
                                                <div className="sm:col-span-2"><InfoFieldEditor label="Competitors (Raw JSON)" field={companyData.competitors || emptyInfoField} onChange={(text) => handleInfoChange('competitors', text)} rows={2} /></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                                <button type="submit" disabled={isLoading || isResearching} className="inline-flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-700 sm:ml-3 sm:w-auto disabled:bg-green-400">
                                    {isLoading ? <LoadingSpinner /> : 'Save'}
                                </button>
                                <button type="button" onClick={onClose} disabled={isLoading || isResearching} className="mt-3 inline-flex w-full justify-center rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-slate-300 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 sm:mt-0 sm:w-auto">
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
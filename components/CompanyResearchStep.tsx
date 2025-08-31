
import React from 'react';
import { CompanyInfoResult, GroundingChunk } from '../types';
import { LoadingSpinner, ArrowRightIcon } from './IconComponents';

interface CompanyResearchStepProps {
  companyInfo: CompanyInfoResult;
  setCompanyInfo: (info: CompanyInfoResult) => void;
  sources: GroundingChunk[];
  onNext: () => void;
  isLoading: boolean;
}

export const CompanyResearchStep = ({ companyInfo, setCompanyInfo, sources, onNext, isLoading }: CompanyResearchStepProps): React.ReactNode => {

    if (isLoading && !companyInfo.mission && !companyInfo.goals) {
        return (
             <div className="flex flex-col items-center justify-center text-center py-24 animate-fade-in">
                 <div className="relative w-16 h-16">
                    <div className="absolute inset-0 bg-blue-200 dark:bg-blue-500/30 rounded-full animate-ping"></div>
                    <svg className="relative w-16 h-16 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                    </svg>
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-6">Researching Company...</h2>
                <p className="mt-2 max-w-md mx-auto text-slate-600 dark:text-slate-400">
                    The AI is gathering the latest intelligence on the company.
                </p>
            </div>
        );
    }
    
    const textareaClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
    
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 3: Company Intelligence</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">The AI has researched the company. Review and edit the findings below.</p>
      </div>
      
       <div className="space-y-4 rounded-lg bg-gray-50 dark:bg-slate-800/80 p-4 border border-slate-200 dark:border-slate-700">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                    <label htmlFor="mission" className="block text-sm font-medium text-slate-500 dark:text-slate-400">Mission</label>
                    <textarea id="mission" value={companyInfo.mission?.text || ''} onChange={(e) => setCompanyInfo({...companyInfo, mission: { text: e.target.value, source: companyInfo.mission?.source || '' }})} className={textareaClass} rows={3}/>
                </div>
                <div className="sm:col-span-2">
                    <label htmlFor="values" className="block text-sm font-medium text-slate-500 dark:text-slate-400">Values</label>
                    <textarea id="values" value={companyInfo.values?.text || ''} onChange={(e) => setCompanyInfo({...companyInfo, values: { text: e.target.value, source: companyInfo.values?.source || '' }})} className={textareaClass} rows={3}/>
                </div>
                <div>
                    <label htmlFor="goals" className="block text-sm font-medium text-slate-500 dark:text-slate-400">Stated Goals</label>
                    <textarea id="goals" value={companyInfo.goals?.text || ''} onChange={(e) => setCompanyInfo({...companyInfo, goals: { text: e.target.value, source: companyInfo.goals?.source || '' }})} className={textareaClass} rows={4}/>
                </div>
                 <div>
                    <label htmlFor="issues" className="block text-sm font-medium text-slate-500 dark:text-slate-400">Challenges / Issues</label>
                    <textarea id="issues" value={companyInfo.issues?.text || ''} onChange={(e) => setCompanyInfo({...companyInfo, issues: { text: e.target.value, source: companyInfo.issues?.source || '' }})} className={textareaClass} rows={4}/>
                </div>
                <div className="sm:col-span-2">
                    <label htmlFor="news" className="block text-sm font-medium text-slate-500 dark:text-slate-400">Recent News</label>
                    <textarea id="news" value={companyInfo.news?.text || ''} onChange={(e) => setCompanyInfo({...companyInfo, news: { text: e.target.value, source: companyInfo.news?.source || '' }})} className={textareaClass} rows={2}/>
                </div>
            </div>
            {sources.length > 0 && (
                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                    <h4 className="text-xs font-medium text-slate-600 dark:text-slate-400">Sources:</h4>
                    <ul className="mt-1 list-disc list-inside space-y-1">
                        {sources.filter(s => s.web?.uri).map(source => (
                            <li key={source.web!.uri}>
                                <a href={source.web!.uri} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 dark:text-blue-400 hover:underline">
                                    {source.web!.title || source.web!.uri}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
      </div>

      <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={onNext}
          disabled={isLoading}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          {isLoading ? <LoadingSpinner /> : 'Next: Final Analysis'}
          {!isLoading && <ArrowRightIcon />}
        </button>
      </div>
    </div>
  );
};

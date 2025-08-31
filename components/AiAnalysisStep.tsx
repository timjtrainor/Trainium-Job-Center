


import React from 'react';
import { ArrowRightIcon, LoadingSpinner } from './IconComponents';
import { KeywordsResult, GuidanceResult, KeywordDetail } from '../types';

interface AiAnalysisStepProps {
  keywords: KeywordsResult | null;
  setKeywords: (keywords: KeywordsResult) => void;
  guidance: GuidanceResult | null;
  setGuidance: (guidance: GuidanceResult) => void;
  problemAnalysis: string;
  setProblemAnalysis: (analysis: string) => void;
  onNext: () => void;
  isLoading: boolean;
}

const EditableSection = ({ title, children }: { title: string, children: React.ReactNode }) => (
  <div className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700 h-full">
    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">{title}</h3>
    <div className="space-y-4">
      {children}
    </div>
  </div>
);

const LabeledTextarea = ({ id, label, value, onChange, rows = 3 }: { id: string, label: string, value: string, onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void, rows?: number }) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-slate-500 dark:text-slate-400">{label}</label>
    <textarea
      id={id}
      value={value}
      onChange={onChange}
      rows={rows}
      className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
    />
  </div>
);

export const AiAnalysisStep = (props: AiAnalysisStepProps): React.ReactNode => {
  const { 
    keywords,
    guidance,
    problemAnalysis,
    onNext, 
    isLoading 
  } = props;
  
  if (isLoading && !problemAnalysis) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-24 animate-fade-in">
         <div className="relative w-16 h-16">
            <div className="absolute inset-0 bg-blue-200 dark:bg-blue-500/30 rounded-full animate-ping"></div>
            <svg className="relative w-16 h-16 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-1.83m-1.5 1.83a6.01 6.01 0 0 1-1.5-1.83m1.5 1.83v-5.25m0 0A2.25 2.25 0 0 1 9.75 9.75M12 12.75c0 .621.504 1.125 1.125 1.125s1.125-.504 1.125-1.125S13.125 11.625 12 11.625 10.875 12.129 10.875 12.75m0-4.5A2.25 2.25 0 0 1 12 6.75" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.41-.04-.81-.1-1.2M15 4.5l-1.5 1.5" />
            </svg>
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-6">Final AI Analysis in Progress</h2>
        <p className="mt-2 max-w-md mx-auto text-slate-600 dark:text-slate-400">
          The AI is extracting keywords, generating resume guidance, and preparing you for the interview.
        </p>
      </div>
    );
  }
  
  const topHardKeywords = [...(keywords?.hard_keywords || [])].sort((a,b) => b.match_strength - a.match_strength).slice(0,4);
  const topSoftKeywords = [...(keywords?.soft_keywords || [])].sort((a,b) => b.match_strength - a.match_strength).slice(0,4);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">AI Guidance</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">Review the AI-generated insights. This information will be used to tailor your resume and prepare for interviews.</p>
      </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <EditableSection title="Top Keywords">
                <h4 className="text-md font-semibold text-slate-700 dark:text-slate-300">Hard Keywords</h4>
                <div className="flex flex-wrap gap-2">
                    {topHardKeywords.map(kw => <span key={kw.keyword} className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">{kw.keyword}</span>)}
                </div>
                 <h4 className="text-md font-semibold text-slate-700 dark:text-slate-300 mt-4">Soft Keywords</h4>
                <div className="flex flex-wrap gap-2">
                    {topSoftKeywords.map(kw => <span key={kw.keyword} className="px-2 py-1 text-xs font-medium rounded-full bg-sky-100 text-sky-800 dark:bg-sky-900/50 dark:text-sky-300">{kw.keyword}</span>)}
                </div>
            </EditableSection>
             <EditableSection title="Resume Guidance">
                <p className="text-sm text-slate-600 dark:text-slate-300">{guidance?.summary.join(' ')}</p>
                <ul className="list-disc pl-5 text-sm space-y-1 text-slate-600 dark:text-slate-300">
                    {guidance?.bullets.map(b => <li key={b}>{b}</li>)}
                </ul>
            </EditableSection>
        </div>
      
      <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={onNext}
          disabled={isLoading}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
        >
          {isLoading ? <LoadingSpinner /> : 'Next: Select Resume'}
          {!isLoading && <ArrowRightIcon />}
        </button>
      </div>
    </div>
  );
};
import React, { useState } from 'react';
import TurndownService from 'turndown';
import { ArrowRightIcon, LoadingSpinner, DocumentTextIcon } from './IconComponents';
import { MarkdownPreview } from './MarkdownPreview';

interface InitialInputStepProps {
  onNext: () => void;
  isLoading: boolean;
  jobLink: string;
  setJobLink: (link: string) => void;
  jobDescription: string;
  setJobDescription: (desc: string) => void;
  isMessageOnlyApp: boolean;
  setIsMessageOnlyApp: (isMessageOnly: boolean) => void;
}

export const InitialInputStep = (props: InitialInputStepProps): React.ReactNode => {
    const { 
        onNext, isLoading, jobLink, setJobLink, jobDescription, setJobDescription,
        isMessageOnlyApp, setIsMessageOnlyApp
    } = props;

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center text-center py-24 animate-fade-in">
                 <div className="relative w-16 h-16">
                    <div className="absolute inset-0 bg-blue-200 dark:bg-blue-500/30 rounded-full animate-ping"></div>
                    <div className="relative w-16 h-16 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                        <DocumentTextIcon className="w-10 h-10" />
                    </div>
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-6">Extracting Job Details...</h2>
                <p className="mt-2 max-w-md mx-auto text-slate-600 dark:text-slate-400">
                    The AI is analyzing the job description to pull out key information. This may take a moment.
                </p>
            </div>
        );
    }

    const [activeTab, setActiveTab] = useState<'edit' | 'preview'>('edit');
    const turndownService = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' });
    
    const handlePaste = (event: React.ClipboardEvent<HTMLTextAreaElement>) => {
        const html = event.clipboardData.getData('text/html');
        if (html) {
            event.preventDefault();
            const markdown = turndownService.turndown(html);
            setJobDescription(markdown);
            setActiveTab('preview'); // Switch to preview after paste for immediate feedback
        } else {
            // Let the default paste happen for plain text
        }
    };
    
    const canProceed = jobDescription.trim();
    const inputClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
    const tabClass = (isActive: boolean) =>
        `px-3 py-1.5 text-sm font-medium rounded-md transition-colors ` +
        (isActive
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
            : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700/50');


  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 1: Provide Job Info</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">Provide a link to the job posting (optional) and paste the full description below for the AI to analyze.</p>
      </div>
      
      <div>
           <label htmlFor="job-link" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Posting Link (Optional)</label>
            <input type="url" id="job-link" value={jobLink} onChange={(e) => setJobLink(e.target.value)} disabled={isLoading}
             className={inputClass} placeholder="https://www.company.com/careers/job-id" />
      </div>

       <div className="relative flex items-start">
            <div className="flex h-6 items-center">
                <input
                    id="message-only-app"
                    name="message-only-app"
                    type="checkbox"
                    checked={isMessageOnlyApp}
                    onChange={(e) => setIsMessageOnlyApp(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
            </div>
            <div className="ml-3 text-sm leading-6">
                <label htmlFor="message-only-app" className="font-medium text-slate-700 dark:text-slate-300">
                    This application uses a profile/pre-uploaded resume and requires a message instead of a file.
                </label>
                <p className="text-xs text-slate-500 dark:text-slate-400">(e.g., Wellfound, LinkedIn Easy Apply)</p>
            </div>
        </div>
      
      <div>
        <div className="flex justify-between items-center">
            <label htmlFor="job-description" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Job Description (Required)
            </label>
            <div className="flex items-center space-x-1 rounded-lg bg-slate-100 dark:bg-slate-800 p-1">
                <button type="button" onClick={() => setActiveTab('edit')} className={tabClass(activeTab === 'edit')}>Edit</button>
                <button type="button" onClick={() => setActiveTab('preview')} className={tabClass(activeTab === 'preview')}>Preview</button>
            </div>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Paste from a job site to auto-format into Markdown.</p>
        <div className="mt-2">
            {activeTab === 'edit' ? (
                 <textarea
                    id="job-description"
                    rows={15}
                    className="w-full p-3 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg font-mono text-xs text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    onPaste={handlePaste}
                    placeholder="Paste the full job description here..."
                    disabled={isLoading}
                />
            ) : (
                <div className="w-full p-3 h-[360px] overflow-y-auto bg-slate-50 dark:bg-slate-700/50 border border-slate-300 dark:border-slate-600 rounded-lg">
                    <MarkdownPreview markdown={jobDescription} />
                </div>
            )}
        </div>
      </div>
      
      <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={onNext}
          disabled={isLoading || !canProceed}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? <LoadingSpinner /> : 'Extract Details with AI'}
          {!isLoading && <ArrowRightIcon />}
        </button>
      </div>
    </div>
  );
};
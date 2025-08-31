import React from 'react';
import { ArrowRightIcon, LoadingSpinner } from './IconComponents';

interface JobDetailsReviewStepProps {
  onNext: () => void;
  isLoading: boolean;
  companyName: string;
  setCompanyName: (name: string) => void;
  companyHomepageUrl: string;
  setCompanyHomepageUrl: (url: string) => void;
  jobTitle: string;
  setJobTitle: (title: string) => void;
  salary: string;
  setSalary: (salary: string) => void;
}

export const JobDetailsReviewStep = (props: JobDetailsReviewStepProps): React.ReactNode => {
    const { 
        onNext, isLoading, companyName, setCompanyName, jobTitle, setJobTitle,
        salary, setSalary, companyHomepageUrl, setCompanyHomepageUrl
    } = props;
    
    const canProceed = companyName.trim() && jobTitle.trim();
    const inputClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";


  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 2: Review Extracted Details</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">The AI has extracted the following details. Please review and edit if necessary before continuing.</p>
      </div>
      
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
           <label htmlFor="company-name" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Company Name</label>
            <input type="text" id="company-name" value={companyName} onChange={(e) => setCompanyName(e.target.value)} disabled={isLoading}
             className={inputClass} />
        </div>
         <div>
           <label htmlFor="company-homepage-url" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Company Homepage URL</label>
            <input type="url" id="company-homepage-url" value={companyHomepageUrl} onChange={(e) => setCompanyHomepageUrl(e.target.value)} disabled={isLoading}
             className={inputClass} placeholder="https://www.company.com" />
        </div>
        <div className="sm:col-span-2">
           <label htmlFor="job-title" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Title</label>
            <input type="text" id="job-title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} disabled={isLoading}
             className={inputClass} />
        </div>
        <div className="sm:col-span-2">
           <label htmlFor="salary" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Salary</label>
            <input type="text" id="salary" value={salary} onChange={(e) => setSalary(e.target.value)} disabled={isLoading}
             className={inputClass} placeholder="e.g., $150,000 - $180,000" />
        </div>
      </div>
      
      <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={onNext}
          disabled={isLoading || !canProceed}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? <LoadingSpinner /> : 'Next: Generate Job Snapshot'}
          {!isLoading && <ArrowRightIcon />}
        </button>
      </div>
    </div>
  );
};
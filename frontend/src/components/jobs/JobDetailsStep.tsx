import React, { useState, useEffect } from 'react';
import { ArrowRightIcon, LoadingSpinner } from '../shared/ui/IconComponents';
import { CompanyInfoResult, StrategicNarrative } from '../../types';
import { MarkdownPreview } from '../shared/ui/MarkdownPreview';

type JobDetailsPayload = {
  companyName: string;
  isRecruitingFirm: boolean;
  jobTitle: string;
  jobLink: string;
  salary: string;
  location: string;
  remoteStatus: 'Remote' | 'Hybrid' | 'On-site' | '';
  jobDescription: string;
}
interface JobDetailsStepProps {
  onNext: (payload: JobDetailsPayload & { narrativeId: string }) => void;
  isLoading: boolean;
  initialJobDetails: JobDetailsPayload;
  narratives: StrategicNarrative[];
  selectedNarrativeId: string;
}

export const JobDetailsStep = (props: JobDetailsStepProps): React.ReactNode => {
    const { 
        onNext, isLoading, initialJobDetails,
        narratives, selectedNarrativeId
    } = props;
    
    const [details, setDetails] = useState(initialJobDetails);
    const [localNarrativeId, setLocalNarrativeId] = useState(selectedNarrativeId);

    useEffect(() => {
        setDetails(initialJobDetails);
        setLocalNarrativeId(selectedNarrativeId);
    }, [initialJobDetails, selectedNarrativeId]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { name, value, type } = e.target;
      const isCheckbox = type === 'checkbox';
      setDetails(prev => ({
        ...prev,
        [name]: isCheckbox ? (e.target as HTMLInputElement).checked : value,
      }));
    };

    const handleNextClick = () => {
      onNext({ ...details, narrativeId: localNarrativeId });
    }
    
    const [jdTab, setJdTab] = useState<'preview' | 'edit'>('preview');

    const canProceed = details.companyName.trim() && details.jobTitle.trim() && details.jobDescription.trim() && localNarrativeId;
    const inputClass = "mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";

    const tabClass = (isActive: boolean) =>
        `px-3 py-1.5 text-sm font-medium rounded-md transition-colors ` +
        (isActive
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
            : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700/50');


  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 2: Review & Refine Job Details</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">The AI has extracted the following details. Please review and edit if necessary.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
           <label htmlFor="companyName" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Company Name</label>
            <input type="text" id="companyName" name="companyName" value={details.companyName} onChange={handleChange} disabled={isLoading}
             className={inputClass} />
        </div>
        <div>
           <label htmlFor="jobTitle" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Title</label>
            <input type="text" id="jobTitle" name="jobTitle" value={details.jobTitle} onChange={handleChange} disabled={isLoading}
             className={inputClass} />
        </div>
        <div className="sm:col-span-2">
           <label htmlFor="jobLink" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Posting Link</label>
            <input type="url" id="jobLink" name="jobLink" value={details.jobLink} onChange={handleChange} disabled={isLoading}
             className={inputClass} />
        </div>
        <div>
           <label htmlFor="salary" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Salary</label>
            <input type="text" id="salary" name="salary" value={details.salary} onChange={handleChange} disabled={isLoading}
             className={inputClass} placeholder="e.g., $150,000 - $180,000" />
        </div>
        <div>
           <label htmlFor="location" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Location</label>
            <input type="text" id="location" name="location" value={details.location} onChange={handleChange} disabled={isLoading}
             className={inputClass} placeholder="e.g., San Francisco, CA" />
        </div>
        <div className="sm:col-span-2">
            <label htmlFor="remoteStatus" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Remote Status</label>
            <select id="remoteStatus" name="remoteStatus" value={details.remoteStatus} onChange={handleChange} disabled={isLoading} className={inputClass}>
                <option value="">Select...</option>
                <option value="On-site">On-site</option>
                <option value="Hybrid">Hybrid</option>
                <option value="Remote">Remote</option>
            </select>
        </div>
        <div className="sm:col-span-2 flex items-center pt-2">
            <input
                type="checkbox"
                id="isRecruitingFirm"
                name="isRecruitingFirm"
                checked={details.isRecruitingFirm}
                onChange={handleChange}
                disabled={isLoading}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="isRecruitingFirm" className="ml-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
                This is a recruiting firm
            </label>
        </div>
      </div>
      
      <div>
        <div className="flex justify-between items-center mb-1">
            <label htmlFor="jobDescription" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Job Description
            </label>
            <div className="flex items-center space-x-1 rounded-lg bg-slate-100 dark:bg-slate-800 p-1">
                <button type="button" onClick={() => setJdTab('edit')} className={tabClass(jdTab === 'edit')}>Edit</button>
                <button type="button" onClick={() => setJdTab('preview')} className={tabClass(jdTab === 'preview')}>Preview</button>
            </div>
        </div>
        <div className="mt-1">
          {jdTab === 'edit' ? (
              <textarea
                id="jobDescription"
                name="jobDescription"
                rows={12}
                className="w-full p-3 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg font-mono text-xs text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                value={details.jobDescription}
                onChange={handleChange}
                placeholder="Paste the full job description here..."
                disabled={isLoading}
              />
          ) : (
             <div className="w-full p-3 h-[305px] overflow-y-auto bg-slate-50 dark:bg-slate-700/50 border border-slate-300 dark:border-slate-600 rounded-lg">
                <MarkdownPreview markdown={details.jobDescription} />
             </div>
          )}
        </div>
      </div>

      <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
        <label htmlFor="narrative-select" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Assign to Narrative <span className="text-red-500">*</span>
        </label>
        <p className="text-xs text-slate-500 dark:text-slate-400">This will associate the application with one of your core career strategies for A/B testing.</p>
        <select
          id="narrative-select"
          value={localNarrativeId}
          onChange={(e) => setLocalNarrativeId(e.target.value)}
          className={`${inputClass} mt-1`}
          disabled={isLoading}
          required
        >
          <option value="">-- Select a Narrative --</option>
          {narratives.map(n => <option key={n.narrative_id} value={n.narrative_id}>{n.narrative_name}</option>)}
        </select>
      </div>
      
      <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={handleNextClick}
          disabled={isLoading || !canProceed}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? <LoadingSpinner /> : 'Next: Confirm Company'}
          {!isLoading && <ArrowRightIcon />}
        </button>
      </div>
    </div>
  );
};
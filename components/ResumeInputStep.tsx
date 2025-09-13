

import React, { useState, useEffect } from 'react';
import { ArrowRightIcon, LoadingSpinner } from './IconComponents';
import { BaseResume, Resume, Prompt, KeywordsResult, UserProfile, ResumeHeader, StrategicNarrative } from '../types';
import { BLANK_RESUME_CONTENT } from '../mockData';
import { useGetResumeContent } from '../hooks/apiHooks';
import { ensureUniqueAchievementIds } from '../utils/resume';

interface SelectResumeStepProps {
  baseResumes: BaseResume[];
  onNext: (resume: Resume) => void;
  isLoading: boolean;
  prompts: Prompt[];
  keywords: KeywordsResult | null;
  userProfile: UserProfile | null;
  applicationNarrative: StrategicNarrative | null;
}

export const SelectResumeStep = ({ baseResumes, onNext, isLoading, keywords, userProfile, applicationNarrative }: SelectResumeStepProps): React.ReactNode => {
    const [selectedResumeId, setSelectedResumeId] = useState<string>('');
    const { refetch: fetchResumeContent } = useGetResumeContent(selectedResumeId, false);
    const [customResumeJson, setCustomResumeJson] = useState<string>(JSON.stringify(BLANK_RESUME_CONTENT, null, 2));
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const defaultResume = baseResumes.find(r => r.resume_id === applicationNarrative?.default_resume_id);
        if (defaultResume) {
          setSelectedResumeId(defaultResume.resume_id);
        } else if (baseResumes.length > 0) {
          setSelectedResumeId(baseResumes[0].resume_id);
        } else {
          setSelectedResumeId('new');
        }
      }, [baseResumes, applicationNarrative?.default_resume_id]);
    
    const handleNext = async () => {
        setError(null);
        let resumeToProcess: Resume | null = null;
        if (selectedResumeId === 'new') {
            try {
                resumeToProcess = JSON.parse(customResumeJson);
            } catch (e) {
                setError("The custom resume JSON is not valid. Please check the format.");
                return;
            }
        } else {
            const foundResume = baseResumes.find(r => r.resume_id.toString() === selectedResumeId);
            if(foundResume) {
                const { data: fullContent } = await fetchResumeContent();
                 if (userProfile && fullContent) {
                    const header: ResumeHeader = {
                        ...fullContent.header, // Keep existing header data
                        // Override with profile data if available
                        first_name: userProfile.first_name || fullContent.header.first_name,
                        last_name: userProfile.last_name || fullContent.header.last_name,
                        job_title: applicationNarrative?.desired_title || fullContent.header.job_title,
                        email: userProfile.email || fullContent.header.email,
                        phone_number: userProfile.phone_number || fullContent.header.phone_number,
                        city: userProfile.city || fullContent.header.city,
                        state: userProfile.state || fullContent.header.state,
                        links: userProfile.links || fullContent.header.links,
                    };
                    resumeToProcess = { ...fullContent, header };
                } else {
                setError("User profile not loaded, cannot proceed.");
                    return;
                }
            }
        }
        
        if (resumeToProcess) {
            resumeToProcess = ensureUniqueAchievementIds(resumeToProcess);
            onNext(resumeToProcess);
        } else {
            setError("Could not find or parse the selected resume.");
        }
    };
    
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Select a Base Resume</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">Choose one of your saved resumes to tailor for this job, or paste a new one.</p>
      </div>

       <div>
        <label htmlFor="resume-select" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Choose Resume
        </label>
        <select
          id="resume-select"
          name="resume-select"
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          value={selectedResumeId}
          onChange={(e) => setSelectedResumeId(e.target.value)}
           disabled={isLoading}
        >
          {baseResumes.map(r => <option key={r.resume_id} value={r.resume_id}>{r.resume_name}</option>)}
          <option value="new">-- Create New Resume --</option>
        </select>
      </div>
      
      {selectedResumeId === 'new' && (
        <div>
            <label htmlFor="resume-json" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            New Resume JSON
            </label>
            <div className="mt-1">
            <textarea
                id="resume-json"
                rows={15}
                className="w-full p-3 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg font-mono text-xs text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                value={customResumeJson}
                onChange={(e) => setCustomResumeJson(e.target.value)}
                disabled={isLoading}
            />
            </div>
        </div>
      )}

       {error && (
          <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
              <p className="text-sm font-medium text-red-800 dark:text-red-300">{error}</p>
          </div>
       )}
      
      <div className="flex items-center justify-end space-x-4 pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          type="button"
          onClick={handleNext}
          disabled={isLoading || !selectedResumeId}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? <LoadingSpinner /> : 'Next: Tailor Resume'}
          {!isLoading && <ArrowRightIcon />}
        </button>
      </div>
    </div>
  );
};
import React, { useEffect, useState } from 'react';
import { Switch } from './Switch';
import { LoadingSpinner } from './IconComponents';
import { WorkflowModeOption, ResetApplicationPayload } from '../types';

interface ResetApplicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: ResetApplicationPayload) => Promise<void> | void;
  initialValues: ResetApplicationPayload;
  isSaving: boolean;
}

const WORKFLOW_MODE_OPTIONS: { value: WorkflowModeOption; label: string; description: string }[] = [
  { value: 'ai_generated', label: 'AI Generated', description: 'Full AI workflow: resume tailoring, analysis, and messaging.' },
  { value: 'fast_track', label: 'Fast Track', description: 'Skip straight to a concise AI summary and outreach message.' },
  { value: 'manual', label: 'Manual AI', description: 'Gather company insights without automated resume tailoring.' },
];

export const ResetApplicationModal: React.FC<ResetApplicationModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialValues,
  isSaving,
}) => {
  const [formState, setFormState] = useState<ResetApplicationPayload>(initialValues);
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setFormState(initialValues);
      setTouched(false);
    }
  }, [isOpen, initialValues]);

  if (!isOpen) {
    return null;
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setTouched(true);
    if (!formState.jobTitle.trim() || !formState.jobDescription.trim()) {
      return;
    }
    await onSubmit(formState);
  };

  const updateField = <K extends keyof ResetApplicationPayload>(key: K, value: ResetApplicationPayload[K]) => {
    setFormState(prev => ({ ...prev, [key]: value }));
  };

  const showValidation = touched && (!formState.jobTitle.trim() || !formState.jobDescription.trim());

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6">
      <div className="relative w-full max-w-3xl rounded-xl bg-white dark:bg-slate-800 shadow-2xl border border-slate-200 dark:border-slate-700">
        <div className="flex items-start justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Reset & Retarget Application</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              Update the targeting details before rerunning the AI workflow. We&apos;ll mark the application as draft and clear previous AI outputs.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-6">
          <section>
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">Workflow Mode</h3>
            <div className="grid gap-3 sm:grid-cols-3">
              {WORKFLOW_MODE_OPTIONS.map(option => {
                const isActive = formState.workflowMode === option.value;
                return (
                  <button
                    type="button"
                    key={option.value}
                    onClick={() => updateField('workflowMode', option.value)}
                    className={`flex flex-col items-start rounded-lg border px-4 py-3 text-left transition shadow-sm ${isActive
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-200'
                        : 'border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-400'
                      }`}
                  >
                    <span className="text-sm font-semibold">{option.label}</span>
                    <span className="mt-1 text-xs text-slate-600 dark:text-slate-400 leading-snug">{option.description}</span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-1">
              <label htmlFor="reset-job-title" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Title</label>
              <input
                id="reset-job-title"
                type="text"
                value={formState.jobTitle}
                onChange={event => updateField('jobTitle', event.currentTarget.value)}
                className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="e.g. Senior Product Manager"
                required
              />
            </div>
            <div className="sm:col-span-1">
              <label htmlFor="reset-job-link" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Job Link</label>
              <input
                id="reset-job-link"
                type="url"
                value={formState.jobLink}
                onChange={event => updateField('jobLink', event.currentTarget.value)}
                className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="https://company.com/jobs/..."
              />
            </div>
          </section>

          <section>
            <label htmlFor="reset-job-description" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Job Description
            </label>
            <textarea
              id="reset-job-description"
              value={formState.jobDescription}
              onChange={event => updateField('jobDescription', event.currentTarget.value)}
              rows={8}
              className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Paste the job description here..."
              required
            />
            {showValidation && (
              <p className="mt-1 text-xs text-red-500">Job title and job description are required to restart the workflow.</p>
            )}
          </section>

          <section className="flex items-center justify-between rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/40 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">Message-only workflow</p>
              <p className="text-xs text-slate-600 dark:text-slate-400">Skip resume tailoring and go straight to outreach prep.</p>
            </div>
            <Switch
              enabled={formState.isMessageOnlyApp}
              onChange={nextValue => updateField('isMessageOnlyApp', nextValue)}
            />
          </section>

          <div className="flex items-center justify-end gap-3 border-t border-slate-200 dark:border-slate-700 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 transition"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition disabled:opacity-70"
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <LoadingSpinner />
                  <span>Updating...</span>
                </>
              ) : (
                'Reset & Restart AI'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

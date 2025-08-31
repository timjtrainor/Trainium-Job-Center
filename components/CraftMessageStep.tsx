import React from 'react';
import { LoadingSpinner, ArrowRightIcon } from './IconComponents';

interface CraftMessageStepProps {
  drafts: string[];
  onSelectDraft: (draft: string) => void;
  finalMessage: string;
  setFinalMessage: (message: string) => void;
  onNext: () => void;
  isLoading: boolean;
}

export const CraftMessageStep = ({
  drafts,
  onSelectDraft,
  finalMessage,
  setFinalMessage,
  onNext,
  isLoading,
}: CraftMessageStepProps): React.ReactNode => {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Craft Your Application Message</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          The AI has generated several drafts based on your profile and the job's core problem. Select one to start, then refine it to perfection.
        </p>
      </div>

      <div className="space-y-4">
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">AI-Generated Drafts</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(drafts || []).map((draft, index) => (
            <div
              key={index}
              className="p-4 rounded-lg border bg-slate-50 dark:bg-slate-800/80 border-slate-200 dark:border-slate-700 space-y-3"
            >
              <p className="text-sm text-slate-600 dark:text-slate-300 italic">"{draft}"</p>
              <div className="text-right">
                <button
                  onClick={() => onSelectDraft(draft)}
                  className="px-3 py-1 text-xs font-semibold rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                >
                  Use This Draft
                </button>
              </div>
            </div>
          ))}
          {(!drafts || drafts.length === 0) && (
             <p className="text-sm text-slate-500 dark:text-slate-400 md:col-span-2 text-center">No drafts generated. This may happen if the AI analysis steps were skipped.</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="final-message" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Final Message to Hiring Team
        </label>
        <textarea
          id="final-message"
          rows={10}
          value={finalMessage}
          onChange={(e) => setFinalMessage(e.target.value)}
          className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="Your refined message will appear here..."
        />
      </div>

      <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={onNext}
          disabled={isLoading || !finalMessage.trim()}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400 disabled:cursor-not-allowed"
        >
          {isLoading ? <LoadingSpinner /> : 'Save Message & Continue'}
          {!isLoading && <ArrowRightIcon />}
        </button>
      </div>
    </div>
  );
};

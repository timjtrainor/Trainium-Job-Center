import React, { useMemo, useState } from 'react';
import { NextStep, Sprint, SprintActionPayload } from '../types';
import { CheckIcon } from './IconComponents';

interface PostSubmitPlanProps {
  summary: string;
  plan: NextStep[];
  onFinish: () => void;
  sprint: Sprint | null;
  onAddActions: (sprintId: string, actions: SprintActionPayload[]) => Promise<void>;
  companyName: string;
  companyId?: string | null;
  jobTitle?: string;
  jobApplicationId?: string | null;
}

export const PostSubmitPlan = ({
  summary,
  plan,
  onFinish,
  sprint,
  onAddActions,
  companyName,
  companyId,
  jobTitle,
  jobApplicationId,
}: PostSubmitPlanProps): React.ReactNode => {
  const [added, setAdded] = useState(false);

  const normalizedPlan = plan ?? [];

  const networkingTitle = useMemo(() => {
    if (companyName) {
      return `${companyName} • ${jobTitle || 'Networking'}`;
    }
    return jobTitle || 'Networking Outreach';
  }, [companyName, jobTitle]);

  const primaryNextMove = useMemo(() => {
    if (normalizedPlan.length === 0) return '';
    const first = normalizedPlan[0];
    if (!first) return '';
    if (first.details && first.details !== first.action) {
      return `${first.action}: ${first.details}`;
    }
    return first.action;
  }, [normalizedPlan]);

  const handleAddToSprint = async () => {
    if (!sprint || added) {
      return;
    }

    const baseOrder = sprint.actions.filter((a) => !a.is_goal).length || 0;
    const impactSections: string[] = [];

    if (summary) {
      impactSections.push(`Why this job: ${summary}`);
    }

    if (primaryNextMove) {
      impactSections.push(`Suggested next move: ${primaryNextMove}`);
    }

    const linkSegments: string[] = [];
    if (jobApplicationId) {
      linkSegments.push(`/application/${jobApplicationId}`);
    }
    if (companyId) {
      linkSegments.push(`/company/${companyId}`);
    }
    if (linkSegments.length > 0) {
      impactSections.push(`Links: ${linkSegments.join(' | ')}`);
    }

    const newAction: SprintActionPayload = {
      title: networkingTitle,
      impact: impactSections.join('\n\n'),
      is_completed: false,
      is_goal: false,
      order_index: baseOrder,
      strategic_tags: ['post-application', 'networking'],
    };

    await onAddActions(sprint.sprint_id, [newAction]);
    setAdded(true);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Post-Submission Action Plan</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          Your application is saved. Use this summary and optional sprint action to drive outreach.
        </p>
      </div>

      <div className="space-y-6">
        <div className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Why This Job? (Your Reference)</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap">{summary}</p>
        </div>

        {normalizedPlan.length > 0 && (
          <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-700">
            <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">Suggested Next Move</h3>
            <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-green-700 dark:text-green-300">
              {normalizedPlan.slice(0, 3).map((item) => (
                <li key={item.step}>
                  <span className="font-semibold">{item.action}</span>
                  {item.details && <span className="block text-sm">{item.details}</span>}
                </li>
              ))}
            </ol>
          </div>
        )}

        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200">Add to Networking Sprint</h3>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Creates a single sprint action linking back to this job so you can batch outreach later.
              </p>
            </div>
            <button
              onClick={handleAddToSprint}
              disabled={!sprint || added}
              className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed"
            >
              {added ? (
                <>
                  <CheckIcon className="h-5 w-5 mr-2" /> Added
                </>
              ) : (
                'Add to Sprint'
              )}
            </button>
          </div>
          {!sprint && (
            <p className="mt-2 text-sm text-blue-700 dark:text-blue-300">
              Create a sprint from the dashboard to start tracking follow-ups.
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          type="button"
          onClick={onFinish}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          Finish & Return to Application Lab
        </button>
      </div>
    </div>
  );
};

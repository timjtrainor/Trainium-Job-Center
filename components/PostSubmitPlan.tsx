import React, { useState } from 'react';
import { NextStep, Sprint, SprintActionPayload } from '../types';
import { CheckIcon } from './IconComponents';

interface PostSubmitPlanProps {
    summary: string;
    plan: NextStep[];
    onFinish: () => void;
    sprint: Sprint | null;
    onAddActions: (sprintId: string, actions: SprintActionPayload[]) => Promise<void>;
    companyName: string;
}

export const PostSubmitPlan = ({ summary, plan, onFinish, sprint, onAddActions, companyName }: PostSubmitPlanProps): React.ReactNode => {
    const [selectedSteps, setSelectedSteps] = useState<number[]>(plan.map(p => p.step));
    const [added, setAdded] = useState(false);

    const handleToggleStep = (stepNumber: number) => {
        setSelectedSteps(prev => 
        prev.includes(stepNumber)
            ? prev.filter(s => s !== stepNumber)
            : [...prev, stepNumber]
        );
    };

    const handleAddToSprint = async () => {
        if (!sprint || selectedSteps.length === 0) return;

        const newActions: SprintActionPayload[] = plan
        .filter(p => selectedSteps.includes(p.step))
        .map((p, index) => ({
            title: `${p.action} for ${companyName}`,
            impact: p.details,
            is_completed: false,
            is_goal: false,
            order_index: (sprint.actions.filter(a => !a.is_goal).length || 0) + index,
            strategic_tags: ['post-application']
        }));
        
        await onAddActions(sprint.sprint_id, newActions);
        setAdded(true);
    };


  return (
    <div className="space-y-6 animate-fade-in">
        <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Post-Submission Action Plan</h2>
            <p className="mt-1 text-slate-600 dark:text-slate-400">Your application is saved. Now, shift immediately from applying to engaging.</p>
        </div>

        <div className="space-y-6">
            <div className="p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Why This Job? (Your Reference)</h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap">{summary}</p>
            </div>

            <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-700">
                <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">Your Next Moves</h3>
                    <button
                        onClick={handleAddToSprint}
                        disabled={!sprint || selectedSteps.length === 0 || added}
                        className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed"
                    >
                        {added ? <><CheckIcon className="h-5 w-5 mr-2"/> Added</> : 'Add to Sprint'}
                    </button>
                </div>
                <div className="mt-3 space-y-4">
                    {(plan || []).map((item) => (
                        <div key={item.step} className="relative flex items-start">
                             <div className="flex h-6 items-center">
                                <input
                                id={`step-${item.step}`}
                                type="checkbox"
                                checked={selectedSteps.includes(item.step)}
                                onChange={() => handleToggleStep(item.step)}
                                className="h-4 w-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
                                />
                            </div>
                            <div className="ml-3 text-sm leading-6">
                                <label htmlFor={`step-${item.step}`} className="font-semibold text-green-800 dark:text-green-100 cursor-pointer">{item.action}</label>
                                <p className="text-green-700 dark:text-green-300">{item.details}</p>
                            </div>
                        </div>
                    ))}
                     {(!plan || plan.length === 0) && <p className="text-sm text-green-700 dark:text-green-300">No next moves generated.</p>}
                </div>
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
import React from 'react';
import { NewAppStep } from '../types';
import { CheckIcon } from './IconComponents';

interface StepTrackerProps {
  currentStep: NewAppStep;
  onStepClick: (step: NewAppStep) => void;
  isMessageOnlyApp: boolean;
  progressData: {
    jobProblemAnalysisResult: any;
    keywords: any;
    finalResume: any;
    applicationQuestions: any[];
    postSubmissionPlan: any;
    applicationMessage?: string;
  };
}

const resumeSteps = [
    { id: NewAppStep.INITIAL_INPUT, name: 'Paste JD' },
    { id: NewAppStep.JOB_DETAILS, name: 'Job Details' },
    { id: NewAppStep.AI_PROBLEM_ANALYSIS, name: 'Problem Analysis' },
    { id: NewAppStep.RESUME_SELECT, name: 'Select Resume' },
    { id: NewAppStep.TAILOR_RESUME, name: 'Tailor Resume' },
    { id: NewAppStep.DOWNLOAD_RESUME, name: 'Download' },
    { id: NewAppStep.ANSWER_QUESTIONS, name: 'Answer Questions' },
    { id: NewAppStep.POST_SUBMIT_PLAN, name: 'Submit Plan' },
];

const messageSteps = [
    { id: NewAppStep.INITIAL_INPUT, name: 'Paste JD' },
    { id: NewAppStep.JOB_DETAILS, name: 'Job Details' },
    { id: NewAppStep.AI_PROBLEM_ANALYSIS, name: 'Problem Analysis' },
    { id: NewAppStep.RESUME_SELECT, name: 'Select Base Resume' },
    { id: NewAppStep.CRAFT_MESSAGE, name: 'Craft Message' },
    { id: NewAppStep.ANSWER_QUESTIONS, name: 'Answer Questions' },
    { id: NewAppStep.POST_SUBMIT_PLAN, name: 'Submit Plan' },
];


const isStepCompleted = (step: NewAppStep, progressData: StepTrackerProps['progressData'], isMessageOnly: boolean): boolean => {
    switch(step) {
        case NewAppStep.INITIAL_INPUT: return true; // Always considered complete if we're past it
        case NewAppStep.JOB_DETAILS: return true;
        case NewAppStep.AI_PROBLEM_ANALYSIS: return !!progressData.keywords;
        case NewAppStep.RESUME_SELECT: return isMessageOnly ? !!progressData.keywords : !!progressData.finalResume;
        case NewAppStep.TAILOR_RESUME: return !!progressData.finalResume;
        case NewAppStep.CRAFT_MESSAGE: return !!progressData.applicationMessage;
        case NewAppStep.DOWNLOAD_RESUME: return !!progressData.finalResume;
        case NewAppStep.ANSWER_QUESTIONS: return progressData.applicationQuestions.length > 0 && !!progressData.postSubmissionPlan; // a bit tricky, let's say if plan is generated, it's done
        case NewAppStep.POST_SUBMIT_PLAN: return !!progressData.postSubmissionPlan;
        default: return false;
    }
}

export const StepTracker = ({ currentStep, onStepClick, isMessageOnlyApp, progressData }: StepTrackerProps): React.ReactNode => {
    const steps = isMessageOnlyApp ? messageSteps : resumeSteps;

    return (
        <nav aria-label="Progress">
            <ol role="list" className="flex items-center space-x-2">
                {steps.map((step, stepIdx) => {
                    const completed = isStepCompleted(step.id, progressData, isMessageOnlyApp) && currentStep > step.id;
                    const isCurrent = currentStep === step.id;
                    
                    return (
                        <li key={step.name} className="relative">
                            <div className="flex items-center text-sm">
                                <button
                                    onClick={() => (completed || isCurrent) && onStepClick(step.id)}
                                    disabled={!completed && !isCurrent}
                                    className={`flex items-center ${completed || isCurrent ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                                >
                                    <span className={`flex h-6 w-6 items-center justify-center rounded-full ${
                                        completed ? 'bg-blue-600' : isCurrent ? 'border-2 border-blue-600 bg-white dark:bg-slate-800' : 'border-2 border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800'
                                    }`}>
                                        {completed ? <CheckIcon className="h-4 w-4 text-white" /> : <span className={`${isCurrent ? 'text-blue-600' : 'text-gray-500 dark:text-slate-400'}`}>{stepIdx + 1}</span>}
                                    </span>
                                    <span className={`ml-2 text-xs font-medium ${
                                        completed ? 'text-slate-700 dark:text-slate-300' : isCurrent ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-slate-400'
                                    }`}>{step.name}</span>
                                </button>
                                {stepIdx !== steps.length - 1 ? (
                                    <div className="absolute right-[-10px] top-3 h-0.5 w-4 bg-gray-200 dark:bg-slate-700" aria-hidden="true" />
                                ) : null}
                            </div>
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
};
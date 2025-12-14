import React, { useState } from 'react';
import { StrategicNarrative, StrategyStep, Prompt, StrategicNarrativePayload } from '../../types';
import { CareerDirectionStep } from './CareerDirectionStep';
import { KnownForStep } from './KnownForStep';
import { ImpactStoryStep } from './ImpactStoryStep';
import { LoadingSpinner } from '../shared/ui/IconComponents';

interface DefineYourStrategyWizardProps {
    narratives: StrategicNarrative[];
    activeNarrative: StrategicNarrative | null;
    activeNarrativeId: string | null;
    onSetNarrative: (id: string | null) => void;
    onSaveNarrative: (payload: StrategicNarrativePayload, narrativeId: string) => Promise<void>;
    onUpdateNarrative: (updatedNarrative: StrategicNarrative) => void;
    prompts: Prompt[];
}

const steps = [
    { id: StrategyStep.CAREER_DIRECTION, name: 'Career Direction' },
    { id: StrategyStep.KNOWN_FOR, name: 'What You\'re Known For' },
    { id: StrategyStep.IMPACT_STORY, name: 'Your Impact Story' },
];

export const DefineYourStrategyWizard = ({ narratives, activeNarrative, activeNarrativeId, onSetNarrative, onSaveNarrative, onUpdateNarrative, prompts }: DefineYourStrategyWizardProps) => {
    
    const [currentStep, setCurrentStep] = useState<StrategyStep>(StrategyStep.CAREER_DIRECTION);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleNarrativeChange = (field: keyof StrategicNarrative, value: any) => {
        if (!activeNarrative) return;
        const updatedNarrative = { ...activeNarrative, [field]: value };
        onUpdateNarrative(updatedNarrative);
    };

    const handleSaveAndNavigate = async (nextStep: StrategyStep) => {
        if (!activeNarrative) return;
        setIsLoading(true);
        setError(null);
        try {
            const { narrative_id, user_id, created_at, updated_at, common_interview_answers, ...payload } = activeNarrative;
            await onSaveNarrative(payload, narrative_id);
            setCurrentStep(nextStep);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to save progress.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleNext = () => {
        if (currentStep < StrategyStep.IMPACT_STORY) {
            handleSaveAndNavigate(currentStep + 1);
        } else {
            handleSaveAndNavigate(currentStep); // Save on the last step
        }
    };

    const handleBack = () => {
        if (currentStep > StrategyStep.CAREER_DIRECTION) {
            handleSaveAndNavigate(currentStep - 1);
        }
    };

    const isNextDisabled = isLoading || !activeNarrative?.desired_title;
    
    const narrativeTabClass = (narrative: StrategicNarrative) => 
        `px-4 py-2 text-sm font-medium rounded-md ` +
        (narrative.narrative_id === activeNarrativeId
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300' 
            : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700/50');

    if (!activeNarrative) {
        return <div>Loading narratives...</div>;
    }

    return (
        <div className="space-y-6">
             <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center space-x-2">
                     {narratives.map((narrative) => (
                        <button key={narrative.narrative_id} onClick={() => onSetNarrative(narrative.narrative_id)} className={narrativeTabClass(narrative)}>
                            {narrative.narrative_name}
                        </button>
                    ))}
                </div>
                <input
                    type="text"
                    value={activeNarrative.narrative_name}
                    onChange={(e) => handleNarrativeChange('narrative_name', e.target.value)}
                    onBlur={() => onSaveNarrative({ narrative_name: activeNarrative.narrative_name }, activeNarrative.narrative_id)}
                    className="text-sm font-semibold bg-white dark:bg-slate-700 p-2 rounded-md border border-slate-300 dark:border-slate-600 focus:ring-blue-500 focus:border-blue-500"
                    aria-label="Edit narrative name"
                />
            </div>
            
            <nav aria-label="Progress">
                <ol role="list" className="space-y-4 md:flex md:space-x-8 md:space-y-0">
                    {steps.map(s => {
                        const isCompleted = s.id < currentStep;
                        const isCurrent = s.id === currentStep;
                        return (
                            <li key={s.name} className="md:flex-1">
                                <div className={`group flex w-full flex-col border-l-4 py-2 pl-4 transition-colors md:border-l-0 md:border-t-4 md:pb-0 md:pl-0 md:pt-4 ${isCurrent ? 'border-blue-600' : isCompleted ? 'border-blue-600' : 'border-gray-200 dark:border-slate-700'}`}>
                                    <span className={`text-sm font-medium transition-colors ${isCurrent || isCompleted ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-slate-400'}`}>{s.name}</span>
                                </div>
                            </li>
                        );
                    })}
                </ol>
            </nav>

            <div className="mt-8 min-h-[300px]">
                {error && <div className="bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300 p-4 rounded-lg my-6" role="alert">{error}</div>}
                
                {currentStep === StrategyStep.CAREER_DIRECTION && <CareerDirectionStep profile={activeNarrative} onProfileChange={handleNarrativeChange} prompts={prompts} />}
                {currentStep === StrategyStep.KNOWN_FOR && <KnownForStep profile={activeNarrative} onProfileChange={handleNarrativeChange} prompts={prompts} />}
                {currentStep === StrategyStep.IMPACT_STORY && <ImpactStoryStep profile={activeNarrative} onProfileChange={handleNarrativeChange} prompts={prompts} />}
            </div>

            <div className="mt-8 flex justify-between pt-6 border-t border-slate-200 dark:border-slate-700">
                <button type="button" onClick={handleBack} disabled={isLoading || currentStep === StrategyStep.CAREER_DIRECTION} className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50 dark:bg-slate-700 dark:text-white dark:ring-slate-600 dark:hover:bg-slate-600">Back</button>
                <button type="button" onClick={handleNext} disabled={isNextDisabled} className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50">
                    {isLoading ? <LoadingSpinner/> : (currentStep === StrategyStep.IMPACT_STORY ? 'Finish & Save' : 'Save & Next')}
                </button>
            </div>
        </div>
    );
};

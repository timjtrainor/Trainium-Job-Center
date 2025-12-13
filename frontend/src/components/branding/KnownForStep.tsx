import React, { useState } from 'react';
import { StrategicNarrative, Prompt } from '../../types';
import { StrategyAiAssistant } from '../StrategyAiAssistant';
import * as geminiService from '../../services/geminiService';
import { TagInput } from '../shared/ui/TagInput';
import { SparklesIcon } from '../shared/ui/IconComponents';

interface KnownForStepProps {
    profile: Partial<StrategicNarrative>;
    onProfileChange: (field: keyof StrategicNarrative, value: any) => void;
    prompts: Prompt[];
}

const labelClass = "block text-sm font-medium text-slate-700 dark:text-slate-300";
const inputClass = "block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm";
const textareaClass = `${inputClass} font-sans`;

type EditableField = 'positioning_statement' | 'key_strengths' | 'signature_capability';

export const KnownForStep = ({ profile, onProfileChange, prompts }: KnownForStepProps) => {
    const [editingField, setEditingField] = useState<EditableField | null>(null);
    const [aiNotes, setAiNotes] = useState('');
    const [aiResult, setAiResult] = useState<any | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    const handleGenerate = async (notes: string) => {
        setIsGenerating(true);
        setAiResult(null);
        try {
            let result;
            if (editingField === 'positioning_statement') {
                const prompt = prompts.find(p => p.id === 'DEFINE_POSITIONING_STATEMENT');
                if (!prompt) throw new Error("DEFINE_POSITIONING_STATEMENT prompt not found.");
                result = await geminiService.definePositioningStatement({ USER_NOTES: notes }, prompt.content);
            } else if (editingField === 'key_strengths') {
                const prompt = prompts.find(p => p.id === 'SUGGEST_KEY_STRENGTHS');
                if (!prompt) throw new Error("SUGGEST_KEY_STRENGTHS prompt not found.");
                result = await geminiService.suggestKeyStrengths({ USER_NOTES: notes }, prompt.content);
            } else if (editingField === 'signature_capability') {
                const prompt = prompts.find(p => p.id === 'DEFINE_SIGNATURE_CAPABILITY');
                if (!prompt) throw new Error("DEFINE_SIGNATURE_CAPABILITY prompt not found.");
                result = await geminiService.defineSignatureCapability({ USER_NOTES: notes }, prompt.content);
            }
            setAiResult(result);
        } catch (error) {
            console.error("AI generation failed", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const useAiResult = (result: any) => {
        if (editingField === 'positioning_statement' && result.suggestion) {
            onProfileChange('positioning_statement', result.suggestion);
        } else if (editingField === 'key_strengths' && result.suggestions) {
            onProfileChange('key_strengths', result.suggestions);
        } else if (editingField === 'signature_capability' && result.suggestion) {
            onProfileChange('signature_capability', result.suggestion);
        }
        setEditingField(null);
        setAiResult(null);
        setAiNotes('');
    };
    
    const openAssistant = (field: EditableField) => {
        if (editingField === field) {
            setEditingField(null); // Toggle off if already open
        } else {
            setEditingField(field);
            setAiNotes('');
            setAiResult(null);
        }
    };

    const renderAssistant = (field: EditableField) => {
        if (editingField !== field) return null;

        let title = '';
        let starterPrompt = '';

        switch (field) {
            case 'positioning_statement':
                title = "Positioning Statement AI";
                starterPrompt = "I'm a product leader focused on B2B SaaS and AI. Help me write a strong positioning statement.";
                break;
            case 'key_strengths':
                title = "Key Strengths AI";
                starterPrompt = "My main skills are in product strategy, data analysis, and team leadership. What are some good ways to phrase these?";
                break;
            case 'signature_capability':
                title = "Signature Capability AI";
                starterPrompt = "I'm good at connecting business needs with technical solutions. How can I say that memorably?";
                break;
        }

        return (
             <div className="pt-2">
                <StrategyAiAssistant
                    title={title}
                    starterPrompt={starterPrompt}
                    userNotes={aiNotes}
                    setUserNotes={setAiNotes}
                    onGenerate={handleGenerate}
                    generationResult={aiResult}
                    onUseResult={useAiResult}
                    isLoading={isGenerating}
                />
             </div>
        )
    };
    
    return (
        <div className="space-y-6 animate-fade-in">
            <p className="text-slate-600 dark:text-slate-400">
                What do you want to be sought out for? This isn't about your past titles — it's about your future focus. Positioning yourself around a specific strength makes you stand out.
            </p>
            <div className="space-y-4">
                <div>
                    <div className="flex justify-between items-center">
                        <label htmlFor="positioning_statement" className={labelClass}>Positioning Statement</label>
                        <button type="button" onClick={() => openAssistant('positioning_statement')} className="p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200" title="Get AI help">
                            <SparklesIcon className="w-5 h-5" />
                        </button>
                    </div>
                    <textarea
                        id="positioning_statement"
                        rows={3}
                        value={profile.positioning_statement || ''}
                        onChange={e => onProfileChange('positioning_statement', e.target.value)}
                        className={textareaClass}
                        placeholder="e.g., A product leader who excels at translating complex technical capabilities into clear customer value, especially in early-stage data and AI products."
                    />
                    {renderAssistant('positioning_statement')}
                </div>
                <div>
                    <div className="flex justify-between items-center">
                        <label className={labelClass}>Key Strengths</label>
                        <button type="button" onClick={() => openAssistant('key_strengths')} className="p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200" title="Get AI help">
                            <SparklesIcon className="w-5 h-5" />
                        </button>
                    </div>
                     <TagInput
                        tags={profile.key_strengths || []}
                        onTagsChange={(tags) => onProfileChange('key_strengths', tags)}
                        placeholder="e.g., Vision Translation, Product Ops"
                    />
                    {renderAssistant('key_strengths')}
                </div>
                <div>
                     <div className="flex justify-between items-center">
                        <label htmlFor="signature_capability" className={labelClass}>Signature Capability</label>
                        <button type="button" onClick={() => openAssistant('signature_capability')} className="p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200" title="Get AI help">
                            <SparklesIcon className="w-5 h-5" />
                        </button>
                    </div>
                    <input
                        type="text"
                        id="signature_capability"
                        value={profile.signature_capability || ''}
                        onChange={e => onProfileChange('signature_capability', e.target.value)}
                        className={inputClass}
                        placeholder="e.g., I make ambiguity actionable."
                    />
                    {renderAssistant('signature_capability')}
                </div>
            </div>
        </div>
    );
};
import React, { useState, useMemo } from 'react';
import { BaseResume, Prompt, StrategicNarrative, StrategicNarrativePayload, CommonInterviewAnswer } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, PlusCircleIcon, ArrowTopRightOnSquareIcon } from './IconComponents';
import { Document, Packer, Paragraph, HeadingLevel } from 'docx';
import saveAs from 'file-saver';
import { InterviewAnswerRefinementPanel } from './InterviewAnswerRefinementPanel';

interface CommonInterviewAnswersTabProps {
    activeNarrative: StrategicNarrative;
    onSaveNarrative: (payload: StrategicNarrativePayload, narrativeId: string) => Promise<void>;
    prompts: Prompt[];
    baseResumes: BaseResume[];
    onGenerateSpeakerNotes: (question: string, answer: string) => Promise<void>;
}

export const CommonInterviewAnswersTab = ({ activeNarrative, onSaveNarrative, prompts, baseResumes, onGenerateSpeakerNotes }: CommonInterviewAnswersTabProps) => {
    const [error, setError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');

    const [isPanelOpen, setIsPanelOpen] = useState(false);
    const [answerToRefine, setAnswerToRefine] = useState<{ answer: CommonInterviewAnswer; index: number } | null>(null);

    const filteredAnswers = useMemo(() => {
        const allAnswers = activeNarrative.common_interview_answers || [];
        if (!searchTerm.trim()) {
            return allAnswers;
        }
        const lowercasedFilter = searchTerm.toLowerCase();
        return allAnswers.filter(qa =>
            qa.question.toLowerCase().includes(lowercasedFilter)
        );
    }, [activeNarrative.common_interview_answers, searchTerm]);
    
    const handleSave = async (newAnswers: CommonInterviewAnswer[]) => {
        try {
            const payloadAnswers = newAnswers.map(({ question, answer, speaker_notes }) => ({ question, answer, speaker_notes }));
            await onSaveNarrative({ common_interview_answers: payloadAnswers }, activeNarrative.narrative_id);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to save.');
        }
    };
    
    const handleAddQuestion = () => {
        const currentAnswers = activeNarrative.common_interview_answers || [];
        const newAnswers = [...currentAnswers, { answer_id: '', user_id: '', narrative_id: activeNarrative.narrative_id, question: 'New Question: What is your greatest strength?', answer: '', speaker_notes: '' }];
        handleSave(newAnswers);
    };

    const handleRemoveQuestion = (index: number) => {
        const currentAnswers = activeNarrative.common_interview_answers || [];
        const newAnswers = currentAnswers.filter((_, i) => i !== index);
        handleSave(newAnswers);
    };
    
    const handleSaveFromPanel = (updatedAnswer: CommonInterviewAnswer) => {
        if (answerToRefine === null) return;
        const { index } = answerToRefine;

        const currentAnswers = activeNarrative.common_interview_answers || [];
        const newAnswers = [...currentAnswers];
        newAnswers[index] = updatedAnswer;
        handleSave(newAnswers);
    };
    
    const handlePopOut = (qa: CommonInterviewAnswer) => {
        const newWindow = window.open('', '_blank', 'width=800,height=600,resizable=yes,scrollbars=yes');
        if (!newWindow) {
            alert('Please allow pop-ups for this site.');
            return;
        }
    
        const escapeHtml = (text: string = '') => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        const textToHtml = (text: string = '') => escapeHtml(text).replace(/\n/g, '<br />');
        const speakerNotesToHtml = (notes: string = '') => {
            if (!notes) return 'No notes.';
            return escapeHtml(notes).replace(/^[-*]\s/gm, '&bull; ').replace(/\n/g, '<br />');
        }
    
        const question = escapeHtml(qa.question);
        const answerHtml = textToHtml(qa.answer);
        const speakerNotesHtml = speakerNotesToHtml(qa.speaker_notes);
    
        const content = `
            <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Answer: ${question.substring(0, 50)}...</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; margin: 0; padding: 2rem; background-color: #f8f9fa; color: #212529; transition: background-color 0.3s, color 0.3s; }
                @media (prefers-color-scheme: dark) { body { background-color: #1e293b; color: #e2e8f0; } .notes { background-color: #334155; } .notes-section { border-top-color: #475569; } h1 { color: #818cf8; } .answer { border-left-color: #475569; } .notes { border-left-color: #818cf8; } }
                .container { max-width: 800px; margin: 0 auto; }
                h1 { font-size: 2em; margin-bottom: 1.5rem; color: #4f46e5; }
                .answer { font-size: 1.1em; white-space: pre-wrap; margin-bottom: 2rem; border-left: 3px solid #cbd5e1; padding-left: 1rem; }
                .notes-section { margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #dee2e6; }
                h2 { font-size: 1.5em; margin-bottom: 1rem; }
                .notes { background-color: #e9ecef; padding: 1rem; border-left: 4px solid #4f46e5; font-family: monospace; font-size: 0.95em; white-space: pre-wrap; border-radius: 4px; }
            </style></head>
            <body><div class="container"><h1>${question}</h1><div class="answer">${answerHtml}</div><div class="notes-section"><h2>Speaker Notes</h2><div class="notes">${speakerNotesHtml}</div></div></div></body></html>`;
        
        newWindow.document.write(content);
        newWindow.document.close();
    };


    const openEditor = (answer: CommonInterviewAnswer, index: number) => {
        setAnswerToRefine({ answer, index });
        setIsPanelOpen(true);
    };

    return (
        <div className="space-y-6 animate-fade-in">
             {isPanelOpen && answerToRefine && (
                <InterviewAnswerRefinementPanel
                    isOpen={isPanelOpen}
                    onClose={() => setIsPanelOpen(false)}
                    answerData={answerToRefine.answer}
                    activeNarrative={activeNarrative}
                    onSave={handleSaveFromPanel}
                    prompts={prompts}
                    onGenerateSpeakerNotes={onGenerateSpeakerNotes}
                />
            )}
            <div className="flex flex-col md:flex-row justify-between items-center mb-4 gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Interview Answer Prep</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Build and refine your core talking points for '{activeNarrative.narrative_name}'.</p>
                </div>
                <div className="flex items-center gap-x-4 w-full md:w-auto">
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Filter by question..."
                        className="w-full md:w-64 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                    <button onClick={handleAddQuestion} className="inline-flex items-center gap-x-1.5 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 flex-shrink-0">
                        <PlusCircleIcon className="h-5 w-5" /> Add Question
                    </button>
                </div>
            </div>
            {error && <p className="text-sm text-red-500 mb-4">{error}</p>}
            <div className="space-y-4">
                {filteredAnswers.map((qa, index) => {
                    const originalIndex = (activeNarrative.common_interview_answers || []).indexOf(qa);
                    return (
                        <div key={qa.answer_id || originalIndex} className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                            <div className="flex justify-between items-start">
                                <h4 className="font-semibold text-slate-800 dark:text-slate-200 flex-grow pr-4">{qa.question}</h4>
                                <div className="flex-shrink-0 flex items-center gap-2">
                                    <button onClick={() => handlePopOut(qa)} className="p-1 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200" title="Open in new window"><ArrowTopRightOnSquareIcon className="h-5 w-5"/></button>
                                    <button onClick={() => openEditor(qa, originalIndex)} className="px-3 py-1 text-sm font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600">Edit</button>
                                </div>
                            </div>
                        </div>
                    )
                })}
                    {filteredAnswers.length === 0 && (
                    <p className="text-center text-slate-500 dark:text-slate-400 py-8">
                        { (activeNarrative.common_interview_answers || []).length > 0
                            ? "No answers match your filter."
                            : "No answers created yet. Click 'Add Question' to start."
                        }
                    </p>
                )}
            </div>
        </div>
    );
};
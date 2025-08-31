import React from 'react';

interface DebugModalProps {
    isOpen: boolean;
    onSend: () => void;
    onContinue: () => void;
    stage: 'request' | 'response';
    prompt: string;
    response: string | null;
}

export const DebugModal = ({ isOpen, onSend, onContinue, stage, prompt, response }: DebugModalProps): React.ReactNode => {
    if (!isOpen) {
        return null;
    }

    const title = stage === 'request' ? 'Confirm AI Prompt' : 'AI Response Received';
    const description = stage === 'request'
        ? 'Review the final prompt being sent to the AI. Click "Send to AI" to proceed.'
        : 'The raw response from the AI is displayed below. Click "Continue" to allow the application to process it.';

    return (
        <div className="relative z-50" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl">
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <h3 className="text-lg font-semibold leading-6 text-slate-900 dark:text-white" id="modal-title">
                                {title}
                            </h3>
                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
                            <div className="mt-4 space-y-4 max-h-[60vh] overflow-y-auto">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Prompt Sent to AI</label>
                                    <textarea
                                        readOnly
                                        value={prompt}
                                        rows={10}
                                        className="w-full p-2 mt-1 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md font-mono text-xs text-slate-700 dark:text-slate-300"
                                    />
                                </div>
                                {stage === 'response' && (
                                     <div>
                                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Raw Response from AI</label>
                                        <textarea
                                            readOnly
                                            value={response || ''}
                                            rows={10}
                                            className="w-full p-2 mt-1 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md font-mono text-xs text-slate-700 dark:text-slate-300"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-slate-800/50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                            {stage === 'request' && (
                                <button type="button" onClick={onSend} className="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto">
                                    Send to AI
                                </button>
                            )}
                             {stage === 'response' && (
                                <button type="button" onClick={onContinue} className="inline-flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 sm:ml-3 sm:w-auto">
                                    Continue
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
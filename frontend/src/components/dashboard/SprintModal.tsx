import React from 'react';
import { Sprint, StrategicNarrative, Prompt, CreateSprintPayload, SprintActionPayload, JobApplication, Contact, LinkedInPost, Message } from '../../types';
import { DailySprintView } from './DailySprintView';
import { XCircleIcon } from '../shared/ui/IconComponents';

interface SprintModalProps {
    isOpen: boolean;
    onClose: () => void;
    // Props for DailySprintView
    sprint: Sprint | null;
    activeNarrative: StrategicNarrative | null;
    prompts: Prompt[];
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
    onCreateSprint: (payload: CreateSprintPayload) => Promise<void>;
    onUpdateSprint: (sprintId: string, payload: Partial<Sprint>) => Promise<void>;
    onUpdateAction: (actionId: string, payload: SprintActionPayload) => Promise<void>;
    onAddActions: (sprintId: string, actions: SprintActionPayload[]) => Promise<void>;
    applications: JobApplication[];
    contacts: Contact[];
    linkedInPosts: LinkedInPost[];
    allMessages: Message[];
}

export const SprintModal = (props: SprintModalProps) => {
    if (!props.isOpen) return null;

    return (
        <div className="relative z-[60]" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div className="relative transform overflow-hidden rounded-lg bg-white dark:bg-slate-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl">
                        <div className="absolute top-0 right-0 pt-4 pr-4">
                            <button
                                type="button"
                                className="rounded-md bg-white dark:bg-slate-800 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                                onClick={props.onClose}
                            >
                                <span className="sr-only">Close</span>
                                <XCircleIcon className="h-6 w-6" />
                            </button>
                        </div>
                        <div className="bg-white dark:bg-slate-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                            <div className="max-h-[85vh] overflow-y-auto pr-4">
                                <DailySprintView {...props} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
import React from 'react';
import { BaseResume, StrategicNarrative } from '../../types';
import { TrashIcon, PlusCircleIcon, LockClosedIcon } from '../shared/ui/IconComponents';

interface ResumesViewProps {
  resumes: BaseResume[];
  activeNarrative: StrategicNarrative | null;
  onAddNew: () => void;
  onEdit: (resume: BaseResume) => void;
  onDelete: (resumeId: string) => void;
  onCopy: (resume: BaseResume) => void;
  onSetDefault: (resumeId: string) => void;
  onToggleLock: (resumeId: string, isCurrentlyLocked: boolean) => void;
  isLoading: boolean;
}

export const ResumesView = ({ resumes, activeNarrative, onAddNew, onEdit, onDelete, onCopy, onSetDefault, onToggleLock, isLoading }: ResumesViewProps): React.ReactNode => {
    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Resume Formulas</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Manage your base resume formulas for targeted applications.</p>
                </div>
                 <button
                    onClick={onAddNew}
                    disabled={isLoading}
                    className="inline-flex items-center justify-center w-full md:w-auto px-5 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
                >
                    <PlusCircleIcon className="w-5 h-5 mr-2 -ml-1" />
                    Create New Resume
                </button>
            </div>
            
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <ul role="list" className="divide-y divide-y-slate-200 dark:divide-slate-700">
                    {resumes.map(resume => {
                        const isDefault = activeNarrative?.default_resume_id === resume.resume_id;
                        return (
                            <li key={resume.resume_id} className="flex items-center justify-between gap-x-6 py-5">
                                <div className="min-w-0">
                                    <div className="flex items-center gap-x-3">
                                        {resume.is_locked && <LockClosedIcon className="h-5 w-5 text-slate-400 flex-shrink-0" />}
                                        <p className="text-sm font-semibold leading-6 text-slate-900 dark:text-white">{resume.resume_name}</p>
                                        {isDefault && (
                                            <span className="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20">
                                                Default
                                            </span>
                                        )}
                                    </div>
                                    <div className="mt-1 flex items-center gap-x-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
                                        <p className="whitespace-nowrap font-mono">ID: {resume.resume_id}</p>
                                    </div>
                                </div>
                                <div className="flex flex-none items-center gap-x-4">
                                     <button
                                        onClick={() => onToggleLock(resume.resume_id, resume.is_locked)}
                                        disabled={isLoading}
                                        className={`rounded-md bg-white dark:bg-slate-700 px-2.5 py-1.5 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 disabled:opacity-50`}
                                    >
                                        {resume.is_locked ? 'Unlock' : 'Lock'}
                                    </button>
                                     {!isDefault && (
                                        <button
                                            onClick={() => onSetDefault(resume.resume_id)}
                                            disabled={isLoading}
                                            className="rounded-md bg-white dark:bg-slate-700 px-2.5 py-1.5 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 disabled:opacity-50"
                                        >
                                            Set as Default
                                        </button>
                                    )}
                                    <button
                                        onClick={() => onCopy(resume)}
                                        disabled={isLoading}
                                        className="rounded-md bg-white dark:bg-slate-700 px-2.5 py-1.5 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 disabled:opacity-50"
                                    >
                                        Copy<span className="sr-only">, {resume.resume_name}</span>
                                    </button>
                                    <button
                                        onClick={() => onEdit(resume)}
                                        disabled={isLoading || resume.is_locked}
                                        className="rounded-md bg-white dark:bg-slate-700 px-2.5 py-1.5 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-slate-600 hover:bg-gray-50 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50 dark:disabled:bg-slate-800"
                                    >
                                        Edit<span className="sr-only">, {resume.resume_name}</span>
                                    </button>
                                     <button
                                        onClick={() => onDelete(resume.resume_id)}
                                        disabled={isLoading || resume.is_locked}
                                        className="rounded-md bg-red-50 dark:bg-red-900/40 px-2.5 py-1.5 text-sm font-semibold text-red-600 dark:text-red-400 shadow-sm ring-1 ring-inset ring-red-300 dark:ring-red-700 hover:bg-red-100 dark:hover:bg-red-900/60 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50"
                                    >
                                        <TrashIcon className="h-4 w-4" />
                                        <span className="sr-only">Delete, {resume.resume_name}</span>
                                    </button>
                                </div>
                            </li>
                        )
                    })}
                    {resumes.length === 0 && (
                        <li className="text-center py-10 text-slate-500 dark:text-slate-400">
                            No resumes found. Click "Create New Resume" to get started.
                        </li>
                    )}
                </ul>
            </div>
        </div>
    );
};
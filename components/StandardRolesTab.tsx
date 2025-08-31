import React, { useState } from 'react';
import { StandardJobRole, StandardJobRolePayload, Prompt, StrategicNarrative } from '../types';
import * as geminiService from '../services/geminiService';
import { PlusCircleIcon, TrashIcon, SparklesIcon, LoadingSpinner } from './IconComponents';

interface StandardRolesTabProps {
    standardRoles: StandardJobRole[];
    activeNarrative: StrategicNarrative | null;
    onCreateStandardRole: (payload: StandardJobRolePayload, narrativeId: string) => Promise<void>;
    onUpdateStandardRole: (roleId: string, payload: StandardJobRolePayload) => Promise<void>;
    onDeleteStandardRole: (roleId: string) => Promise<void>;
    prompts: Prompt[];
}

const RoleCard = ({ role, onUpdate, onDelete, prompts }: { role: StandardJobRole, onUpdate: (id: string, payload: StandardJobRolePayload) => void, onDelete: (id: string) => void, prompts: Prompt[] }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editableRole, setEditableRole] = useState(role);
    const [isExpanding, setIsExpanding] = useState(false);

    const handleSave = () => {
        onUpdate(role.role_id, { role_title: editableRole.role_title, role_description: editableRole.role_description });
        setIsEditing(false);
    };

    const handleExpandDescription = async () => {
        setIsExpanding(true);
        const prompt = prompts.find(p => p.id === 'EXPAND_ROLE_DESCRIPTION');
        if (!prompt) {
            console.error("Expand role description prompt not found");
            setIsExpanding(false);
            return;
        }

        try {
            const result = await geminiService.expandRoleDescription({ ROLE_DESCRIPTION_NOTES: editableRole.role_description }, prompt.content);
            setEditableRole(prev => ({ ...prev, role_description: result.expanded_description }));
        } catch (error) {
            console.error("Failed to expand description", error);
        } finally {
            setIsExpanding(false);
        }
    };

    if (isEditing) {
        return (
            <div className="p-4 bg-slate-100 dark:bg-slate-900/50 rounded-lg border border-slate-300 dark:border-slate-600 space-y-3">
                <input
                    type="text"
                    value={editableRole.role_title}
                    onChange={(e) => setEditableRole({ ...editableRole, role_title: e.target.value })}
                    className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm font-semibold"
                />
                 <div className="relative">
                    <textarea
                        value={editableRole.role_description}
                        onChange={(e) => setEditableRole({ ...editableRole, role_description: e.target.value })}
                        rows={5}
                        className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm pr-10"
                    />
                    <button
                        type="button"
                        onClick={handleExpandDescription}
                        disabled={isExpanding}
                        className="absolute top-2 right-2 p-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200 disabled:opacity-50"
                        title="Expand with AI"
                    >
                        {isExpanding ? <LoadingSpinner /> : <SparklesIcon className="h-5 w-5" />}
                    </button>
                </div>
                <div className="flex justify-end gap-2">
                    <button onClick={() => setIsEditing(false)} className="px-3 py-1 text-sm font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600">Cancel</button>
                    <button onClick={handleSave} className="px-3 py-1 text-sm font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700">Save</button>
                </div>
            </div>
        );
    }

    return (
        <div className="p-4 bg-white dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="flex justify-between items-start">
                <div>
                    <h4 className="font-bold text-slate-800 dark:text-slate-200">{role.role_title}</h4>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">{role.role_description}</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-2 flex-shrink-0 ml-4">
                    <button onClick={() => setIsEditing(true)} className="px-2.5 py-1 text-xs font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600">Edit</button>
                    <button onClick={() => onDelete(role.role_id)} className="p-1.5 text-xs font-semibold rounded-md text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/40 ring-1 ring-inset ring-red-200 dark:ring-red-700 hover:bg-red-100 dark:hover:bg-red-900/60"><TrashIcon className="h-4 w-4" /></button>
                </div>
            </div>
        </div>
    );
};


export const StandardRolesTab = ({ standardRoles, activeNarrative, onCreateStandardRole, onUpdateStandardRole, onDeleteStandardRole, prompts }: StandardRolesTabProps) => {
    const [newRoleTitle, setNewRoleTitle] = useState('');
    const [newRoleRoleDescription, setNewRoleRoleDescription] = useState('');
    const [isAdding, setIsAdding] = useState(false);

    const handleAddRole = async () => {
        if (!newRoleTitle.trim() || !activeNarrative) return;
        
        await onCreateStandardRole({
            role_title: newRoleTitle,
            role_description: newRoleRoleDescription
        }, activeNarrative.narrative_id);
        
        setNewRoleTitle('');
        setNewRoleRoleDescription('');
        setIsAdding(false);
    };

    return (
        <div className="space-y-6">
            <p className="text-slate-600 dark:text-slate-400">
                Define standard roles to help the AI understand unstated expectations for jobs you apply to. For example, a 'Senior Product Manager' role implies responsibilities like 'Mentoring junior PMs' and 'Presenting to executive leadership', even if they aren't in the job description.
            </p>
            
            <div className="space-y-4">
                {standardRoles.map(role => (
                    <RoleCard key={role.role_id} role={role} onUpdate={onUpdateStandardRole} onDelete={onDeleteStandardRole} prompts={prompts} />
                ))}
            </div>

            {isAdding ? (
                <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 space-y-3">
                     <h4 className="font-semibold text-slate-800 dark:text-slate-200">New Standard Role</h4>
                     <input
                        type="text"
                        value={newRoleTitle}
                        onChange={(e) => setNewRoleTitle(e.target.value)}
                        placeholder="Role Title (e.g., Senior Product Manager)"
                        className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm font-semibold"
                    />
                    <textarea
                        value={newRoleRoleDescription}
                        onChange={(e) => setNewRoleRoleDescription(e.target.value)}
                        rows={3}
                        placeholder="Brief notes about responsibilities (AI can expand this later)"
                        className="block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                    <div className="flex justify-end gap-2">
                        <button onClick={() => setIsAdding(false)} className="px-3 py-1 text-sm font-semibold rounded-md bg-white dark:bg-slate-700 ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600">Cancel</button>
                        <button onClick={handleAddRole} className="px-3 py-1 text-sm font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700">Add Role</button>
                    </div>
                </div>
            ) : (
                <button
                    onClick={() => setIsAdding(true)}
                    className="w-full flex justify-center items-center gap-2 py-3 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition"
                >
                    <PlusCircleIcon className="h-5 w-5" />
                    Add Standard Role
                </button>
            )}
        </div>
    );
};
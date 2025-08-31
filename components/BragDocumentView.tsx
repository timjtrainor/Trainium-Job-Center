import React, { useState } from 'react';
import { BragBankEntry, BragBankEntryPayload, StrategicNarrative, Prompt, PromptContext } from '../types';
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from 'docx';
import saveAs from 'file-saver';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, PlusCircleIcon, TrashIcon, SparklesIcon, ArrowDownTrayIcon } from './IconComponents';

interface BragDocumentViewProps {
    items: BragBankEntry[];
    onSave: (itemData: BragBankEntryPayload, itemId?: string) => Promise<void>;
    onDelete: (itemId: string) => Promise<void>;
    strategicNarratives: StrategicNarrative[];
    prompts: Prompt[];
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}

const ImpactQuantifierPanel = ({
    item,
    onClose,
    onSave,
    prompts,
    debugCallbacks
}: {
    item: BragBankEntry;
    onClose: () => void;
    onSave: (updatedItem: BragBankEntryPayload, itemId: string) => void;
    prompts: Prompt[];
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}) => {
    const [conversation, setConversation] = useState<{ author: 'user' | 'ai', text: string }[]>([]);
    const [userInput, setUserInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [currentDescription, setCurrentDescription] = useState(item.description);

    const callAI = async (history: { author: 'user' | 'ai', text: string }[]) => {
        setIsLoading(true);
        const prompt = prompts.find(p => p.id === 'QUANTIFY_IMPACT');
        if (!prompt) {
            console.error("QUANTIFY_IMPACT prompt not found.");
            setIsLoading(false);
            return;
        }

        try {
            const context: PromptContext = {
                RAW_TEXT: item.description || item.title,
                CONVERSATION_HISTORY: history.map(m => `${m.author}: ${m.text}`).join('\n'),
            };

            const response = await geminiService.quantifyImpact(context, prompt.content, debugCallbacks);

            try {
                // If response is JSON, it's suggestions
                const parsed = JSON.parse(response);
                if(parsed.suggestions) {
                    setSuggestions(parsed.suggestions);
                }
            } catch(e) {
                // Otherwise, it's a follow-up question
                setConversation(prev => [...prev, { author: 'ai', text: response }]);
            }
        } catch (error) {
            console.error("Error quantifying impact:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useState(() => {
        callAI([]);
    });

    const handleSend = () => {
        const newHistory = [...conversation, { author: 'user' as const, text: userInput }];
        setConversation(newHistory);
        setUserInput('');
        callAI(newHistory);
    };

    const handleUseSuggestion = (suggestion: string) => {
        setCurrentDescription(suggestion);
        setSuggestions([]); // Clear suggestions after one is chosen
    };

    return (
         <div className="mt-4 p-4 bg-slate-100 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
             <h4 className="font-semibold text-slate-800 dark:text-slate-200">Impact Quantifier AI</h4>
            <div className="mt-2 space-y-2 h-48 overflow-y-auto pr-2">
                {conversation.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.author === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <p className={`p-2 rounded-lg text-sm max-w-md ${msg.author === 'user' ? 'bg-blue-100 dark:bg-blue-900/50' : 'bg-white dark:bg-slate-700'}`}>{msg.text}</p>
                    </div>
                ))}
            </div>
            {suggestions.length > 0 ? (
                <div className="mt-2 space-y-2">
                    <p className="text-sm font-semibold">Here are some rewritten versions:</p>
                    {suggestions.map((s, i) => (
                        <div key={i} className="flex items-center justify-between p-2 bg-white dark:bg-slate-700 rounded-md">
                            <p className="text-sm italic">{s}</p>
                            <button onClick={() => handleUseSuggestion(s)} className="text-xs font-bold text-green-600 hover:underline ml-2">USE</button>
                        </div>
                    ))}
                </div>
            ) : (
                 <div className="mt-2 flex gap-2">
                    <input type="text" value={userInput} onChange={e => setUserInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} placeholder="Answer the AI's question..." className="w-full p-2 text-sm rounded-md" />
                    <button onClick={handleSend} disabled={isLoading} className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-md disabled:opacity-50">{isLoading ? <LoadingSpinner/> : 'Send'}</button>
                </div>
            )}
            <div className="mt-4 flex justify-end gap-2">
                <button onClick={onClose} className="px-3 py-1 text-sm rounded-md">Cancel</button>
                <button onClick={() => onSave({ ...item, description: currentDescription }, item.entry_id)} className="px-3 py-1 text-sm bg-green-600 text-white rounded-md">Save Changes</button>
            </div>
        </div>
    )
};


export const BragDocumentView = ({ items, onSave, onDelete, strategicNarratives, prompts, debugCallbacks }: BragDocumentViewProps) => {
    const [newItem, setNewItem] = useState<BragBankEntryPayload>({ title: '', description: '', tags: [], source_context: '' });
    const [editingItemId, setEditingItemId] = useState<string | null>(null);

    const handleExport = () => {
        const docChildren: Paragraph[] = [new Paragraph({ text: "My Brag Document", heading: HeadingLevel.TITLE })];
        
        items.forEach(item => {
            docChildren.push(new Paragraph({ text: item.title, heading: HeadingLevel.HEADING_2, spacing: { before: 200 } }));
            if (item.description) {
                docChildren.push(new Paragraph({ text: item.description }));
            }
            if(item.tags) {
                docChildren.push(new Paragraph({ text: `Tags: ${item.tags.join(', ')}`, run: { italics: true } }));
            }
        });

        const doc = new Document({ sections: [{ children: docChildren }] });

        Packer.toBlob(doc).then(blob => {
            saveAs(blob, "BragDocument.docx");
        });
    };

    const handleSaveNew = async (e: React.FormEvent) => {
        e.preventDefault();
        await onSave(newItem);
        setNewItem({ title: '', description: '', tags: [], source_context: '' });
    };

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Brag Bank</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Your private log of accomplishments, ready for performance reviews and resume updates.</p>
                </div>
                <button onClick={handleExport} className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-sm">
                    <ArrowDownTrayIcon className="h-5 w-5"/> Export to Word
                </button>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <form onSubmit={handleSaveNew} className="space-y-4">
                    <h2 className="text-xl font-bold">Log a New Win</h2>
                    <div>
                        <label className="text-sm font-medium">Title / Headline</label>
                        <input type="text" value={newItem.title} onChange={e => setNewItem({...newItem, title: e.target.value})} className="w-full p-2 mt-1 rounded-md" required />
                    </div>
                    <div>
                        <label className="text-sm font-medium">Description</label>
                        <textarea value={newItem.description || ''} onChange={e => setNewItem({...newItem, description: e.target.value})} rows={3} className="w-full p-2 mt-1 rounded-md" required />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-medium">Tags (comma separated)</label>
                            <input type="text" value={(newItem.tags || []).join(', ')} onChange={e => setNewItem({...newItem, tags: e.target.value.split(',').map(t => t.trim())})} className="w-full p-2 mt-1 rounded-md" placeholder="e.g., Leadership, Q3-2024" />
                        </div>
                         <div>
                            <label className="text-sm font-medium">Source / Context</label>
                            <input type="text" value={newItem.source_context || ''} onChange={e => setNewItem({...newItem, source_context: e.target.value})} className="w-full p-2 mt-1 rounded-md" placeholder="e.g., Project Titan Launch" />
                        </div>
                    </div>
                    <div className="text-right">
                        <button type="submit" className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 shadow-sm">
                            <PlusCircleIcon className="h-5 w-5"/> Add Item
                        </button>
                    </div>
                </form>
            </div>

            <div className="space-y-4">
                {items.map(item => (
                    <div key={item.entry_id} className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-4 border border-slate-200 dark:border-slate-700">
                        <div className="flex justify-between items-start">
                            <div className="flex-grow">
                                <p className="font-semibold text-slate-800 dark:text-slate-200">{item.title}</p>
                                <p className="mt-1 text-sm">{item.description}</p>
                                <div className="mt-2 flex flex-wrap gap-2">
                                    {(item.tags || []).map(tag => <span key={tag} className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">{tag}</span>)}
                                </div>
                            </div>
                            <div className="flex-shrink-0 ml-4 flex gap-2">
                                <button onClick={() => setEditingItemId(item.entry_id)} className="p-1 text-blue-500" title="Quantify with AI"><SparklesIcon className="h-5 w-5"/></button>
                                <button onClick={() => onDelete(item.entry_id)} className="p-1 text-red-500" title="Delete"><TrashIcon className="h-5 w-5"/></button>
                            </div>
                        </div>
                        {editingItemId === item.entry_id && <ImpactQuantifierPanel item={item} onClose={() => setEditingItemId(null)} onSave={onSave} prompts={prompts} debugCallbacks={debugCallbacks} />}
                    </div>
                ))}
            </div>
        </div>
    );
};

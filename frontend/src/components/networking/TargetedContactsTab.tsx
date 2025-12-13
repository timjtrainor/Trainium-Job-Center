import React, { useState, useMemo, useRef } from 'react';
import { Contact, StrategicNarrative } from '../../types';
import { PlusCircleIcon, TrashIcon } from '../shared/ui/IconComponents';
import { Switch } from '../shared/ui/Switch';

interface TargetedContactsTabProps {
  contacts: Contact[];
  activeNarrative: StrategicNarrative | null;
  onOpenContactModal: (contact?: Contact | null) => void;
  onImportContacts: (fileContent: string) => Promise<void>;
  onDeleteContact: (contactId: string) => void;
}

const getStatusClassName = (statusName: string) => {
  const baseClass = "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset";
  const statusMap: { [key: string]: string } = {
    'To Contact': 'bg-gray-50 text-gray-600 ring-gray-500/10 dark:bg-gray-400/10 dark:text-gray-400 dark:ring-gray-400/20',
    'Connection Sent': 'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20',
    'In Conversation': 'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20',
    'Follow-up Needed': 'bg-yellow-50 text-yellow-800 ring-yellow-600/20 dark:bg-yellow-400/10 dark:text-yellow-500 dark:ring-yellow-400/20',
    'Not a Fit': 'bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-400/10 dark:text-red-400 dark:ring-red-400/20',
    'No Response': 'bg-orange-50 text-orange-700 ring-orange-600/20 dark:bg-orange-400/10 dark:text-orange-400 dark:ring-orange-400/20',
  };
  return `${baseClass} ${statusMap[statusName] || 'bg-gray-50 text-gray-600 ring-gray-500/10'}`;
};

export const TargetedContactsTab = ({ contacts, activeNarrative, onOpenContactModal, onImportContacts, onDeleteContact }: TargetedContactsTabProps): React.ReactNode => {
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [showStrategicOnly, setShowStrategicOnly] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const uniqueStatuses = useMemo(() => Array.from(new Set(contacts.map(c => c.status))), [contacts]);

    const filteredContacts = useMemo(() => {
        const narrativeContacts = contacts.filter(c => {
            if (!activeNarrative) return true; // Show all if no narrative is active
            if (!c.strategic_narratives || c.strategic_narratives.length === 0) return true; // Show contacts not assigned to any narrative
            return c.strategic_narratives.some(n => n.narrative_id === activeNarrative.narrative_id);
        });

        return narrativeContacts.filter(contact => {
            const lowerSearchTerm = searchTerm.toLowerCase();
            const fullName = `${contact.first_name} ${contact.last_name}`.toLowerCase();
            const companyName = contact.company_name?.toLowerCase() || '';
            
            const matchesSearch = searchTerm.trim() === '' ||
                fullName.includes(lowerSearchTerm) ||
                (contact.job_title && contact.job_title.toLowerCase().includes(lowerSearchTerm)) ||
                companyName.includes(lowerSearchTerm);
            
            const matchesStatus = statusFilter === 'all' || contact.status === statusFilter;

            const score = contact.strategic_alignment_score || 0;
            const matchesStrategic = !showStrategicOnly || score >= 7;

            return matchesSearch && matchesStatus && matchesStrategic;
        });
    }, [contacts, searchTerm, statusFilter, showStrategicOnly, activeNarrative]);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const content = e.target?.result as string;
                onImportContacts(content);
            };
            reader.readAsText(file);
        }
    };

    const handleImportClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Targeted Contacts</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Manage contacts for the '{activeNarrative?.narrative_name}' narrative.</p>
                </div>
                <div className="flex items-center gap-2">
                     <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        className="hidden"
                        accept=".csv"
                    />
                     <button onClick={handleImportClick} className="px-4 py-2 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-600 shadow-sm">Import CSV</button>
                    <button onClick={() => onOpenContactModal(null)} className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-sm">
                        <PlusCircleIcon className="w-5 h-5 mr-2 -ml-1" />
                        Add New Contact
                    </button>
                </div>
            </div>
            <div className="flex flex-col sm:flex-row items-center justify-between my-6 gap-4">
                <div className="w-full sm:w-1/2">
                    <input type="text" placeholder="Search by name, title, or company..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm" />
                </div>
                <div className="flex items-center gap-4 w-full sm:w-auto">
                    <div className="flex items-center">
                        <Switch enabled={showStrategicOnly} onChange={setShowStrategicOnly} />
                        <span className="ml-2 text-sm font-medium text-slate-700 dark:text-slate-300 whitespace-nowrap">High Fit Only (&gt;7)</span>
                    </div>
                    <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-full sm:w-auto rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm">
                        <option value="all">All Statuses</option>
                        {uniqueStatuses.map(status => <option key={status} value={status}>{status}</option>)}
                    </select>
                </div>
            </div>
            <div className="-mx-6 sm:-mx-8 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead className="bg-slate-50 dark:bg-slate-800">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Name</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Title & Company</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Strategic Fit</th>
                            <th className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                        {filteredContacts.map(contact => {
                            const score = contact.strategic_alignment_score || 0;
                            return (
                                <tr key={contact.contact_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 group">
                                    <td className="px-6 py-4 whitespace-nowrap cursor-pointer" onClick={() => onOpenContactModal(contact)}>
                                        <div className="text-sm font-medium text-slate-900 dark:text-white">{contact.first_name} {contact.last_name}</div>
                                        <div className="text-xs text-slate-500 dark:text-slate-400">{contact.persona}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap cursor-pointer" onClick={() => onOpenContactModal(contact)}>
                                        <div className="text-sm text-slate-600 dark:text-slate-300">{contact.job_title}</div>
                                        <div className="text-xs text-slate-500 dark:text-slate-400">{contact.company_name || 'N/A'}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm cursor-pointer" onClick={() => onOpenContactModal(contact)}>
                                        <span className={getStatusClassName(contact.status)}>{contact.status}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm cursor-pointer" onClick={() => onOpenContactModal(contact)}>
                                        <div className="flex items-center">
                                            <div className="w-20 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                                                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${score * 10}%` }}></div>
                                            </div>
                                            <span className="ml-2 font-semibold">{score.toFixed(1)}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                         <button onClick={() => onDeleteContact(contact.contact_id)} className="p-1 text-slate-400 hover:text-red-500 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 opacity-0 group-hover:opacity-100 transition-opacity" title="Delete Contact"><TrashIcon className="h-5 w-5" /></button>
                                    </td>
                                </tr>
                            )
                        })}
                        {contacts.length > 0 && filteredContacts.length === 0 && (
                            <tr><td colSpan={5} className="text-center py-10 text-slate-500 dark:text-slate-400">No contacts match your filters.</td></tr>
                        )}
                        {contacts.length === 0 && (
                             <tr><td colSpan={5} className="text-center py-10 text-slate-500 dark:text-slate-400">No contacts yet for this narrative.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

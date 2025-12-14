

import React, { useState, useMemo } from 'react';
import { Contact, UserProfile } from '../../types';
import { PlusCircleIcon } from '../shared/ui/IconComponents';
import { Switch } from '../shared/ui/Switch';

interface NetworkingViewProps {
  contacts: Contact[];
  userProfile: UserProfile | null;
  onOpenContactModal: (contact?: Contact | null) => void;
}

const getStatusClassName = (statusName: string) => {
  const baseClass = "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset";
  const statusMap: { [key: string]: string } = {
    'To Contact': 'bg-gray-50 text-gray-600 ring-gray-500/10 dark:bg-gray-400/10 dark:text-gray-400 dark:ring-gray-400/20',
    'Connection Sent': 'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20',
    'In Conversation': 'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20',
    'Follow-up Needed': 'bg-yellow-50 text-yellow-800 ring-yellow-600/20 dark:bg-yellow-400/10 dark:text-yellow-500 dark:ring-yellow-400/20',
    'Not a Fit': 'bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-400/10 dark:text-red-400 dark:ring-red-400/20',
  };
  return `${baseClass} ${statusMap[statusName] || 'bg-gray-50 text-gray-600 ring-gray-500/10'}`;
};

export const NetworkingView = ({ contacts, userProfile, onOpenContactModal }: NetworkingViewProps): React.ReactNode => {
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [showStrategicOnly, setShowStrategicOnly] = useState(false);

    const uniqueStatuses = useMemo(() => ['To Contact', 'Connection Sent', 'In Conversation', 'Follow-up Needed', 'Not a Fit'], []);

    const filteredContacts = useMemo(() => {
        return contacts.filter(contact => {
            const lowerSearchTerm = searchTerm.toLowerCase();
            const fullName = `${contact.first_name} ${contact.last_name}`.toLowerCase();
            const companyName = contact.company_name?.toLowerCase() || '';

            const matchesSearch = searchTerm.trim() === '' ||
                fullName.includes(lowerSearchTerm) ||
                (contact.job_title && contact.job_title.toLowerCase().includes(lowerSearchTerm)) ||
                companyName.includes(lowerSearchTerm);
            
            const matchesStatus = statusFilter === 'all' || contact.status === statusFilter;

            const score = contact.strategic_alignment_score || 0;
            const matchesStrategic = !showStrategicOnly || score >= 5;

            return matchesSearch && matchesStatus && matchesStrategic;
        });
    }, [contacts, searchTerm, statusFilter, showStrategicOnly]);

    return (
        <div className="space-y-6 animate-fade-in">
             <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Reaction Network</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Catalyze professional bonds and track your networking reactions.</p>
                </div>
                 <button
                    onClick={() => onOpenContactModal(null)}
                    className="inline-flex items-center justify-center w-full md:w-auto px-5 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                    <PlusCircleIcon className="w-5 h-5 mr-2 -ml-1" />
                    Add New Contact
                </button>
            </div>

            {/* Contacts Table */}
             <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Contacts</h2>
                <div className="flex flex-col sm:flex-row items-center justify-between my-6 gap-4">
                    <div className="w-full sm:w-1/2">
                        <input
                            type="text"
                            placeholder="Search by name, title, or company..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        />
                    </div>
                    <div className="flex items-center gap-4 w-full sm:w-auto">
                        <div className="flex items-center">
                           <Switch enabled={showStrategicOnly} onChange={setShowStrategicOnly} />
                           <span className="ml-2 text-sm font-medium text-slate-700 dark:text-slate-300">Show Strategic Contacts Only</span>
                        </div>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full sm:w-auto rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        >
                            <option value="all">All Statuses</option>
                            {uniqueStatuses.map(status => (
                                <option key={status} value={status}>{status}</option>
                            ))}
                        </select>
                    </div>
                </div>
                <div className="-mx-6 sm:-mx-8 overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                        <thead className="bg-slate-50 dark:bg-slate-800">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Name</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Title</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Company</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Strategic Fit</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                            {filteredContacts.map(contact => {
                                const score = contact.strategic_alignment_score || 0;
                                const isIdeal = score >= 8;
                                const rowClass = isIdeal ? 'bg-green-50 dark:bg-green-900/20' : '';
                                return (
                                <tr key={contact.contact_id} className={`hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer ${rowClass}`} onClick={() => onOpenContactModal(contact)}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-white">{contact.first_name} {contact.last_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 dark:text-slate-300">{contact.job_title}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">{contact.company_name || 'N/A'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <span className={getStatusClassName(contact.status)}>
                                            {contact.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <div className="flex items-center">
                                            <div className="w-20 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                                                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${score * 10}%` }}></div>
                                            </div>
                                            <span className="ml-2 font-semibold">{score.toFixed(1)}</span>
                                        </div>
                                    </td>
                                </tr>
                            )})}
                            {contacts.length === 0 && (
                                <tr><td colSpan={5} className="text-center py-10 text-slate-500">No contacts yet.</td></tr>
                            )}
                            {contacts.length > 0 && filteredContacts.length === 0 && (
                                <tr><td colSpan={5} className="text-center py-10 text-slate-500">No contacts match your filters.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
             </div>
        </div>
    );
};
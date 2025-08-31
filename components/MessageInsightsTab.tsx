import React, { useState, useMemo } from 'react';
import { Message, Contact } from '../types';

interface MessageInsightsTabProps {
    messages: Message[];
    contacts: Contact[];
    onViewMessage: (message: Message) => void;
}

const KpiCard = ({ title, value, subValue }: { title: string; value: string; subValue?: string; }) => (
    <div className="bg-white dark:bg-slate-800/80 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400 truncate">{title}</p>
        <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">{value}</p>
        {subValue && <p className="text-xs text-slate-500 dark:text-slate-400">{subValue}</p>}
    </div>
);

export const MessageInsightsTab = ({ messages, contacts, onViewMessage }: MessageInsightsTabProps) => {
    const [filterType, setFilterType] = useState('all');

    const sentMessages = useMemo(() => messages.filter(m => m.message_type !== 'Note' && m.is_user_sent), [messages]);

    const metrics = useMemo(() => {
        const repliedContacts = new Set(contacts.filter(c => c.status === 'In Conversation').map(c => c.contact_id));
        
        let repliedMessages = 0;
        const contactMessageMap = new Map<string, boolean>();

        for (const message of sentMessages) {
            if (message.contact_id && !contactMessageMap.has(message.contact_id)) {
                if (repliedContacts.has(message.contact_id)) {
                    repliedMessages++;
                    contactMessageMap.set(message.contact_id, true);
                }
            }
        }
        
        const uniqueContactsMessaged = new Set(sentMessages.map(m => m.contact_id).filter(Boolean)).size;
        
        const responseRate = uniqueContactsMessaged > 0 ? (repliedMessages / uniqueContactsMessaged) * 100 : 0;
        
        const connectionMessages = sentMessages.filter(m => m.message_type === 'Connection');
        // This is a simplification. A real acceptance rate would need more data.
        const acceptedConnections = new Set(contacts.filter(c => ['In Conversation', 'Follow-up Needed'].includes(c.status)).map(c => c.contact_id));
        const acceptedCount = connectionMessages.filter(m => m.contact_id && acceptedConnections.has(m.contact_id)).length;
        const connectionAcceptanceRate = connectionMessages.length > 0 ? (acceptedCount / connectionMessages.length) * 100 : 0;

        const messageTypeCounts = sentMessages.reduce((acc, msg) => {
            acc[msg.message_type] = (acc[msg.message_type] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);
        
        const mostEffectiveType = Object.entries(messageTypeCounts).sort((a,b) => b[1] - a[1])[0]?.[0] || 'N/A';

        return {
            totalSent: sentMessages.length,
            responseRate: responseRate.toFixed(1) + '%',
            connectionAcceptanceRate: connectionAcceptanceRate.toFixed(1) + '%',
            mostEffectiveType
        };
    }, [sentMessages, contacts]);

    const filteredMessages = useMemo(() => {
        if (filterType === 'all') return sentMessages;
        return sentMessages.filter(m => m.message_type === filterType);
    }, [sentMessages, filterType]);

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <KpiCard title="Total Messages Sent" value={metrics.totalSent.toString()} />
                <KpiCard title="Overall Response Rate" value={metrics.responseRate} />
                <KpiCard title="Connection Acceptance" value={metrics.connectionAcceptanceRate} subValue="(Estimated)" />
                <KpiCard title="Most Sent Type" value={metrics.mostEffectiveType} />
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold">Message History</h3>
                    <select
                        value={filterType}
                        onChange={e => setFilterType(e.target.value)}
                        className="rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    >
                        <option value="all">All Types</option>
                        <option value="Connection">Connection</option>
                        <option value="Follow-up">Follow-up</option>
                        <option value="Comment">Comment</option>
                    </select>
                </div>
                <div className="-mx-6 sm:-mx-8 overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                         <thead className="bg-slate-50 dark:bg-slate-800">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Recipient</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Message Preview</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Type</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Replied?</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                            {filteredMessages.map(msg => {
                                const contact = contacts.find(c => c.contact_id === msg.contact_id);
                                const hasReplied = contact?.status === 'In Conversation';
                                return (
                                <tr key={msg.message_id} onClick={() => onViewMessage(msg)} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-white">
                                        {contact ? `${contact.first_name} ${contact.last_name}` : 'N/A'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400 max-w-sm truncate">{msg.content}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">{msg.message_type}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">{new Date(msg.created_at).toLocaleDateString()}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">{hasReplied ? '✅' : '❌'}</td>
                                </tr>
                            )})}
                            {filteredMessages.length === 0 && (
                                <tr><td colSpan={5} className="text-center py-10 text-slate-500">No messages found.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
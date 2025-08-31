import React, { useState, useMemo } from 'react';
import { LinkedInEngagement, Contact, StrategicNarrative } from '../types';
import { PlusCircleIcon } from './IconComponents';

interface PostEngagementTabProps {
  engagements: LinkedInEngagement[];
  contacts: Contact[];
  activeNarrative: StrategicNarrative | null;
  onOpenContactModal: (contact?: Partial<Contact> | null) => void;
  onAddEngagement: () => void;
}

const calculateStrategicFit = (engagement: { contact_title: string; }, profile: StrategicNarrative | null): number => {
    if (!profile) return 0;
    let score = 0;
    const contactText = `${engagement.contact_title}`.toLowerCase();
    
    // Desired Title match (+5)
    if (profile.desired_title && contactText.includes(profile.desired_title.toLowerCase())) {
        score += 5;
    }

    // Key Strengths match (+1 per match, max 5)
    let strengthMatches = 0;
    if (profile.key_strengths) {
        for (const strength of profile.key_strengths) {
            if (contactText.includes(strength.toLowerCase())) {
                strengthMatches++;
            }
        }
    }
    score += Math.min(strengthMatches, 5);
    
    return Math.min(score, 10);
};

const InteractionBadge = ({ type }: { type: 'like' | 'comment' | 'share' }) => {
    const typeMap = {
        like: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300',
        comment: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
        share: 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300',
    };
    return <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-md ${typeMap[type]}`}>{type}</span>;
}

export const PostEngagementTab = ({ engagements, contacts, activeNarrative, onOpenContactModal, onAddEngagement }: PostEngagementTabProps): React.ReactNode => {
    const engagementsWithScores = useMemo(() => {
        return engagements.map(engagement => ({
            ...engagement,
            strategicFit: calculateStrategicFit(engagement, activeNarrative)
        })).sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }, [engagements, activeNarrative]);
    
    const handleMessage = (engagement: LinkedInEngagement) => {
        // Try to find an existing contact
        const existingContact = contacts.find(c => 
            (c.first_name && c.last_name && `${c.first_name} ${c.last_name}` === engagement.contact_name)
        );

        if (existingContact) {
            onOpenContactModal(existingContact);
        } else {
             const [firstName, ...lastNameParts] = engagement.contact_name.split(' ');
             const lastName = lastNameParts.join(' ');
             onOpenContactModal({
                first_name: firstName,
                last_name: lastName,
                job_title: engagement.contact_title,
                notes: `Saw they ${engagement.interaction_type}d your post about "${engagement.post_theme}"`,
             });
        }
    };

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
             <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Who's Engaging With Your Content</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Manually track likes, comments, and shares to identify warm leads.</p>
                </div>
                <button
                    onClick={onAddEngagement}
                    className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                >
                    <PlusCircleIcon className="w-5 h-5 mr-2 -ml-1" />
                    Add Engagement
                </button>
            </div>
            
            <div className="-mx-6 sm:-mx-8 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead className="bg-slate-50 dark:bg-slate-800">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Person</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Engagement</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Post Theme</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Strategic Fit</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Date</th>
                            <th className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                        </tr>
                    </thead>
                     <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                        {engagementsWithScores.map(engagement => {
                            const isIdeal = engagement.strategicFit >= 8;
                            const rowClass = isIdeal ? 'bg-green-50 dark:bg-green-900/20' : '';
                            return (
                                <tr key={engagement.engagement_id} className={rowClass}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-slate-900 dark:text-white">{engagement.contact_name}</div>
                                        <div className="text-sm text-slate-500 dark:text-slate-400">{engagement.contact_title}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm"><InteractionBadge type={engagement.interaction_type} /></td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400 max-w-xs truncate">{engagement.post_theme}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                         <div className="flex items-center">
                                            <div className="w-20 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                                                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${engagement.strategicFit * 10}%` }}></div>
                                            </div>
                                            <span className="ml-2 font-semibold">{engagement.strategicFit.toFixed(1)}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">{new Date(engagement.created_at).toLocaleDateString()}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button onClick={() => handleMessage(engagement)} className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-200">Message</button>
                                    </td>
                                </tr>
                            )
                        })}
                         {engagementsWithScores.length === 0 && (
                            <tr><td colSpan={6} className="text-center py-10 text-slate-500">No engagements tracked yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
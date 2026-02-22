

import React, { useState, useMemo } from 'react';
import { Contact, UserProfile } from '../types';
import { PlusCircleIcon } from './IconComponents';
import { Switch } from './Switch';
import { NetworkingLeaderboard } from './NetworkingLeaderboard';

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

export const NetworkingView = (): React.ReactNode => {
    return (
        <div className="space-y-10 animate-fade-in">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">Networking Strategy Hub</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">High-Growth Networking Opportunities prioritize your outreach based on Antidote DNA leverage.</p>
                </div>
            </div>

            {/* Hero Section: Networking Tournament */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900 rounded-2xl p-6 border border-blue-100 dark:border-slate-700 shadow-sm">
                <NetworkingLeaderboard />
            </div>
        </div>
    );
};
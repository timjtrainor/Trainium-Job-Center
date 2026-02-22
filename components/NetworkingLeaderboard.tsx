import React, { useEffect, useState } from 'react';
import { LeaderboardEntry } from '../types';
import { getLeaderboard, removeFromLeaderboard, recalculateLeaderboard } from '../services/apiService';
import { useNavigate } from 'react-router-dom';
import { TrophyIcon, TrashIcon, ArrowPathIcon, SparklesIcon, ChevronRightIcon, UsersIcon, BuildingOfficeIcon } from './IconComponents';

export const NetworkingLeaderboard: React.FC = () => {
    const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [recalculateDays, setRecalculateDays] = useState(1);
    const navigate = useNavigate();

    const loadData = async () => {
        setLoading(true);
        try {
            const data = await getLeaderboard();
            setEntries(data);
        } catch (error) {
            console.error('Failed to load leaderboard:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleRemove = async (id: string) => {
        if (!confirm('Remove this opportunity from the leaderboard?')) return;
        try {
            await removeFromLeaderboard(id);
            setEntries(prev => prev.filter(e => e.job_application_id !== id));
        } catch (error) {
            console.error('Failed to remove entry:', error);
        }
    };

    const handleRecalculate = async () => {
        setRefreshing(true);
        try {
            await recalculateLeaderboard(recalculateDays);
            await loadData();
        } catch (error) {
            console.error('Failed to recalculate:', error);
        } finally {
            setRefreshing(false);
        }
    };

    if (loading && entries.length === 0) {
        return (
            <div className="flex h-64 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                        <TrophyIcon className="h-6 w-6" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Tournament Leaderboard</h2>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Top 10 High-Growth Networking Opportunities</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg px-2 py-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 mr-2">History</span>
                        <input
                            type="number"
                            value={recalculateDays}
                            onChange={(e) => setRecalculateDays(parseInt(e.target.value) || 30)}
                            className="w-12 bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-300 focus:outline-none"
                            min="1"
                            max="365"
                        />
                        <span className="text-[10px] font-bold text-slate-400 ml-1">Days</span>
                    </div>
                    <button
                        onClick={handleRecalculate}
                        disabled={refreshing}
                        className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 disabled:bg-blue-400 transition-colors shadow-sm min-w-[140px] justify-center"
                    >
                        <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                        {refreshing ? 'Ranking...' : 'Rank Opportunities'}
                    </button>
                </div>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800 overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/50 shadow-sm">
                {entries.length === 0 ? (
                    <div className="p-12 text-center text-slate-500">
                        No opportunities ranked yet. Submit new jobs to see the tournament in action.
                    </div>
                ) : (
                    entries.map((entry) => (
                        <div
                            key={entry.job_application_id}
                            className="group relative flex flex-col sm:flex-row sm:items-center gap-4 p-5 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-all"
                        >
                            {/* Rank Indicator */}
                            <div className="flex items-center gap-4 sm:w-16">
                                <span className={`flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold shadow-sm
                                    ${entry.rank === 1 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400' :
                                        entry.rank === 2 ? 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300' :
                                            entry.rank === 3 ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400' :
                                                'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-500'}`}
                                >
                                    #{entry.rank}
                                </span>
                            </div>

                            {/* Main Content */}
                            <div className="flex-1 space-y-2">
                                <div className="flex items-start justify-between gap-2">
                                    <div>
                                        <h3 className="font-bold text-slate-900 dark:text-white leading-snug">
                                            {entry.job_title}
                                        </h3>
                                        {entry.company_name && (
                                            <div className="flex items-center gap-2">
                                                <p className="text-xs font-medium text-blue-600 dark:text-blue-400">
                                                    {entry.company_name}
                                                </p>
                                                {entry.contact_count !== undefined && entry.contact_count > 0 && (
                                                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                                                        <UsersIcon className="h-3 w-3" />
                                                        {entry.contact_count}
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                    <button
                                        onClick={() => handleRemove(entry.job_application_id)}
                                        className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 transition-all"
                                        title="Remove from leaderboard"
                                    >
                                        <TrashIcon className="h-4 w-4" />
                                    </button>
                                </div>

                                {entry.pov_hook && (
                                    <div className="flex items-start gap-2 rounded-lg bg-blue-50/50 p-3 dark:bg-blue-900/10">
                                        <SparklesIcon className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                                        <p className="text-sm italic text-slate-600 dark:text-slate-300 leading-relaxed">
                                            "{entry.pov_hook}"
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div className="flex items-center gap-2 sm:pl-4">
                                <button
                                    onClick={() => navigate(`/application/${entry.job_application_id}`)}
                                    className="flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition-all"
                                >
                                    <BuildingOfficeIcon className="h-4 w-4" />
                                    Networking Intel
                                </button>
                                <button
                                    onClick={() => navigate(`/application/${entry.job_application_id}`)}
                                    className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/40 dark:text-blue-400 dark:hover:bg-blue-900/60 transition-all"
                                    title="View Strategy"
                                >
                                    <ChevronRightIcon className="h-5 w-5" />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

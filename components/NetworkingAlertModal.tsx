import React from 'react';
import { LeaderboardAlert } from '../types';
import { TrophyIcon, XMarkIcon, SparklesIcon, ArrowRightIcon } from './IconComponents';

interface NetworkingAlertModalProps {
    alert: LeaderboardAlert | null;
    onClose: () => void;
    onViewLeaderboard: () => void;
}

export const NetworkingAlertModal: React.FC<NetworkingAlertModalProps> = ({ alert, onClose, onViewLeaderboard }) => {
    if (!alert) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-300">
            <div
                className="relative w-full max-w-lg overflow-hidden rounded-3xl border border-white/20 bg-white/10 p-8 shadow-2xl backdrop-blur-xl animate-in zoom-in-95 duration-500"
                style={{
                    background: 'linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%)',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(255,255,255,0.1)'
                }}
            >
                {/* Decorative background glow */}
                <div className="absolute -top-24 -right-24 h-48 w-48 rounded-full bg-blue-500/20 blur-3xl" />
                <div className="absolute -bottom-24 -left-24 h-48 w-48 rounded-full bg-indigo-500/20 blur-3xl" />

                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 text-white/60 hover:text-white transition-colors"
                >
                    <XMarkIcon className="h-6 w-6" />
                </button>

                <div className="text-center space-y-6">
                    <div className="inline-flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30 animate-bounce-subtle">
                        <TrophyIcon className="h-10 w-10 text-white" />
                    </div>

                    <div className="space-y-2">
                        <h2 className="text-3xl font-bold tracking-tight text-white">
                            High-Value Networking Match!
                        </h2>
                        <p className="text-lg text-blue-100/80">
                            This opportunity just hit <span className="text-blue-400 font-bold">Top {alert.rank}</span> on your leaderboard.
                        </p>
                    </div>

                    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/20 p-6 text-left">
                        <div className="flex items-start gap-4">
                            <div className="mt-1 flex-shrink-0">
                                <SparklesIcon className="h-5 w-5 text-blue-400" />
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-blue-400/80">
                                    Strategic POV Hook
                                </span>
                                <p className="text-sm italic leading-relaxed text-white/90">
                                    "{alert.pov_hook}"
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col gap-3 pt-4">
                        <button
                            onClick={onViewLeaderboard}
                            className="flex w-full items-center justify-center gap-2 rounded-xl bg-white px-6 py-4 text-sm font-bold text-slate-900 shadow-lg hover:bg-blue-50 transition-all active:scale-[0.98]"
                        >
                            View Networking Leaderboard
                            <ArrowRightIcon className="h-4 w-4" />
                        </button>
                        <button
                            onClick={onClose}
                            className="w-full text-sm font-medium text-white/60 hover:text-white transition-colors py-2"
                        >
                            Close and Continue
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

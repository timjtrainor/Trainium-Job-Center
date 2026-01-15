import React from 'react';
import { CompanyPathology, ConsultativeBridge } from '../../types';
import { ExclamationCircleIcon, ShieldCheckIcon, ArrowLongRightIcon } from '@heroicons/react/24/outline';

interface PathologyAntidoteViewProps {
    pathology: CompanyPathology;
    bridge: ConsultativeBridge;
}

const RISK_COLORS = {
    'Low': 'text-green-600 bg-green-50 border-green-200 dark:text-green-400 dark:bg-green-900/20 dark:border-green-800',
    'Medium': 'text-yellow-600 bg-yellow-50 border-yellow-200 dark:text-yellow-400 dark:bg-yellow-900/20 dark:border-yellow-800',
    'High': 'text-orange-600 bg-orange-50 border-orange-200 dark:text-orange-400 dark:bg-orange-900/20 dark:border-orange-800',
    'Critical': 'text-red-600 bg-red-50 border-red-200 dark:text-red-400 dark:bg-red-900/20 dark:border-red-800',
};

export const PathologyAntidoteView: React.FC<PathologyAntidoteViewProps> = ({ pathology, bridge }) => {
    if (!pathology || !bridge) {
        return (
            <div className="p-8 text-center bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700">
                <p className="text-slate-500 dark:text-slate-400 text-sm italic">
                    Pathology analysis and consultative bridge data not available for this strategy.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Pathology (Problem) */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-red-100 dark:border-red-900/30 p-6 shadow-sm relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1 h-full bg-red-400/50" />
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                            <ExclamationCircleIcon className="h-5 w-5" />
                            <h3 className="font-bold text-sm uppercase tracking-wide">Diagonosed Pathology</h3>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${RISK_COLORS[pathology.risk_level]}`}>
                            {pathology.risk_level} Risk
                        </span>
                    </div>

                    <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors">
                        "{pathology.name}"
                    </h2>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 leading-relaxed">
                        {pathology.diagnosis}
                    </p>

                    <div>
                        <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Key Symptoms</h4>
                        <div className="flex flex-wrap gap-2">
                            {pathology.symptoms.map((symptom, i) => (
                                <span key={i} className="px-2 py-1 bg-red-50 dark:bg-red-900/10 text-red-700 dark:text-red-300 text-xs rounded border border-red-100 dark:border-red-900/20">
                                    {symptom}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Antidote (Solution) */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-emerald-100 dark:border-emerald-900/30 p-6 shadow-sm relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1 h-full bg-emerald-400/50" />
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                            <ShieldCheckIcon className="h-5 w-5" />
                            <h3 className="font-bold text-sm uppercase tracking-wide">Your Antidote</h3>
                        </div>
                    </div>

                    <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                        "{bridge.antidote_theme}"
                    </h2>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 leading-relaxed">
                        {bridge.narrative_arc}
                    </p>

                    <div>
                        <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Bridge Talking Points</h4>
                        <ul className="space-y-2">
                            {bridge.key_talking_points.map((point, i) => (
                                <li key={i} className="flex gap-2 text-xs text-slate-700 dark:text-slate-300">
                                    <ArrowLongRightIcon className="h-4 w-4 text-emerald-500 shrink-0" />
                                    {point}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>

            {/* Visual connector (optional, can be CSS arrow) */}
        </div>
    );
};

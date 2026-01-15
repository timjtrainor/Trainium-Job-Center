import React from 'react';
import { SelectedStory } from '../../types';
import { StarIcon, SparklesIcon } from '@heroicons/react/24/solid';

interface StoryBankSelectorProps {
    stories: SelectedStory[];
}

export const StoryBankSelector: React.FC<StoryBankSelectorProps> = ({ stories }) => {
    if (!stories) return null;
    return (
        <div className="space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                <StarIcon className="h-4 w-4 text-amber-400" />
                Selected "Kill-Shot" Stories
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {stories.map((story, index) => (
                    <div key={index} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer group">
                        <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-bold px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
                                Story #{index + 1}
                            </span>
                            <SparklesIcon className="h-4 w-4 text-slate-300 group-hover:text-amber-400 transition-colors" />
                        </div>

                        <h4 className="font-bold text-slate-900 dark:text-white mb-2 line-clamp-2">
                            {story.title}
                        </h4>

                        <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 line-clamp-3">
                            {story.relevance}
                        </p>

                        <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-100 dark:border-blue-900/20">
                            <p className="text-[10px] uppercase font-bold text-blue-500 mb-1">Transition Hook</p>
                            <p className="text-xs text-blue-900 dark:text-blue-100 italic">
                                "{story.custom_hook}"
                            </p>
                        </div>
                    </div>
                ))}

                {stories.length === 0 && (
                    <div className="col-span-3 text-center py-8 text-slate-400 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
                        No stories selected yet. Generate a strategy to find your best matches.
                    </div>
                )}
            </div>
        </div>
    );
};

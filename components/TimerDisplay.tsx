import React from 'react';

interface TimerDisplayProps {
    elapsedSeconds: number;
}

export const TimerDisplay = ({ elapsedSeconds }: TimerDisplayProps): React.ReactNode => {
    const minutes = Math.floor(elapsedSeconds / 60);
    const seconds = elapsedSeconds % 60;

    const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

    let colorClass = 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300';
    if (elapsedSeconds >= 300 && elapsedSeconds < 600) { // 5 to 10 minutes
        colorClass = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300';
    } else if (elapsedSeconds >= 600) { // Over 10 minutes
        colorClass = 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300';
    }

    return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full font-mono text-sm font-semibold ${colorClass}`}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{formattedTime}</span>
        </div>
    );
};
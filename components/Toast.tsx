import React, { useEffect, useState } from 'react';
import { Toast, ToastType } from '../types';

const ICONS: Record<ToastType, React.ElementType> = {
    success: ({ className }: { className: string }) => (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    ),
    error: ({ className }: { className: string }) => (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    ),
    info: ({ className }: { className: string }) => (
         <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    ),
    warning: ({ className }: { className: string }) => (
        <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
    ),
};

const TYPE_CLASSES: Record<ToastType, { bg: string; text: string; icon: string }> = {
    success: {
        bg: 'bg-green-50 dark:bg-green-900/50',
        text: 'text-green-800 dark:text-green-200',
        icon: 'text-green-500 dark:text-green-400',
    },
    error: {
        bg: 'bg-red-50 dark:bg-red-900/50',
        text: 'text-red-800 dark:text-red-200',
        icon: 'text-red-500 dark:text-red-400',
    },
    info: {
        bg: 'bg-blue-50 dark:bg-blue-900/50',
        text: 'text-blue-800 dark:text-blue-200',
        icon: 'text-blue-500 dark:text-blue-400',
    },
    warning: {
        bg: 'bg-yellow-50 dark:bg-yellow-900/50',
        text: 'text-yellow-800 dark:text-yellow-200',
        icon: 'text-yellow-500 dark:text-yellow-400',
    },
};

export const ToastComponent = ({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) => {
    const [isExiting, setIsExiting] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsExiting(true);
            setTimeout(onDismiss, 300); // Allow time for exit animation
        }, 5000); // Auto-dismiss after 5 seconds

        return () => clearTimeout(timer);
    }, [onDismiss]);

    const handleDismiss = () => {
        setIsExiting(true);
        setTimeout(onDismiss, 300);
    };

    const Icon = ICONS[toast.type];
    const classes = TYPE_CLASSES[toast.type];
    
    const animationClass = isExiting ? 'animate-fade-out-right' : 'animate-fade-in-right';

    return (
        <div className={`w-full max-w-sm p-4 rounded-lg shadow-lg flex items-start ${classes.bg} ${animationClass}`}>
            <div className="flex-shrink-0">
                <Icon className={`h-6 w-6 ${classes.icon}`} />
            </div>
            <div className="ml-3 flex-1">
                <p className={`text-sm font-medium ${classes.text}`}>{toast.message}</p>
            </div>
            <div className="ml-4 flex-shrink-0 flex">
                 <button onClick={handleDismiss} className={`inline-flex rounded-md p-1.5 ${classes.text} hover:bg-black/10 focus:outline-none focus:ring-2 focus:ring-offset-2 ${classes.bg} focus:ring-current`}>
                    <span className="sr-only">Dismiss</span>
                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                </button>
            </div>
        </div>
    );
};

import React, { createContext, useState, useContext, useCallback, ReactNode, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Toast, ToastType } from '../types';

interface ToastContextType {
    addToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
};

interface ToastProviderProps {
    children: ReactNode;
}

export const ToastProvider = ({ children }: ToastProviderProps) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((message: string, type: ToastType = 'info') => {
        const id = uuidv4();
        setToasts(prevToasts => [...prevToasts, { id, message, type }]);
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ addToast }}>
            {children}
            <div className="fixed top-4 right-4 z-[100] w-full max-w-xs space-y-3">
                {toasts.map(toast => (
                    <ToastComponent key={toast.id} toast={toast} onDismiss={() => removeToast(toast.id)} />
                ))}
            </div>
        </ToastContext.Provider>
    );
};

const ToastComponent = ({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) => {
    useEffect(() => {
        const timer = setTimeout(() => {
            onDismiss();
        }, 5000); // Auto-dismiss after 5 seconds

        return () => {
            clearTimeout(timer);
        };
    }, [onDismiss]);

    const baseClasses = 'w-full max-w-sm p-4 rounded-lg shadow-lg flex items-center';
    const typeClasses = {
        success: 'bg-green-100 dark:bg-green-900/80 text-green-800 dark:text-green-200',
        error: 'bg-red-100 dark:bg-red-900/80 text-red-800 dark:text-red-200',
        info: 'bg-blue-100 dark:bg-blue-900/80 text-blue-800 dark:text-blue-200',
        warning: 'bg-yellow-100 dark:bg-yellow-900/80 text-yellow-800 dark:text-yellow-200',
    };

    return (
        <div className={`${baseClasses} ${typeClasses[toast.type]} animate-fade-in-right`}>
            <span className="text-sm font-medium flex-1">{toast.message}</span>
            <button onClick={onDismiss} className="ml-4 p-1 rounded-full hover:bg-black/10">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    );
};
import React, { createContext, useState, useContext, useCallback, ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Toast, ToastType } from '../types';
import { ToastComponent } from '../components/shared/ui/Toast';

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

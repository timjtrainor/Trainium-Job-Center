import React from 'react';

interface SwitchProps {
    enabled: boolean;
    onChange: (enabled: boolean) => void;
}

export const Switch = ({ enabled, onChange }: SwitchProps): React.ReactNode => {
    const srOnlyText = enabled ? 'Disable' : 'Enable';
    return (
        <button
            type="button"
            className={`${
                enabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-slate-700'
            } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-800`}
            role="switch"
            aria-checked={enabled}
            onClick={() => onChange(!enabled)}
        >
            <span className="sr-only">{srOnlyText}</span>
            <span
                aria-hidden="true"
                className={`${
                    enabled ? 'translate-x-5' : 'translate-x-0'
                } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
            />
        </button>
    );
};
import React, { useState } from 'react';

interface TagInputProps {
    tags: string[];
    onTagsChange: (tags: string[]) => void;
    placeholder?: string;
    label?: string;
    disabled?: boolean;
}

export const TagInput = ({ tags, onTagsChange, placeholder = 'Add tags...', label, disabled }: TagInputProps): React.ReactNode => {
    const [inputValue, setInputValue] = useState('');

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const newTag = inputValue.trim();
            if (newTag && !tags.includes(newTag)) {
                onTagsChange([...tags, newTag]);
            }
            setInputValue('');
        }
    };

    const removeTag = (tagToRemove: string) => {
        onTagsChange(tags.filter(tag => tag !== tagToRemove));
    };

    return (
        <div>
            {label && <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{label}</label>}
            <div className="flex flex-wrap items-center gap-2 p-2 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700">
                {tags.map((tag, index) => (
                    <div key={index} className="flex items-center gap-1 bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300 text-sm font-medium px-2 py-1 rounded-full">
                        <span>{tag}</span>
                        <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            disabled={disabled}
                            className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200 focus:outline-none"
                        >
                            &times;
                        </button>
                    </div>
                ))}
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={disabled}
                    className="flex-grow bg-transparent focus:outline-none text-sm p-1"
                    placeholder={placeholder}
                />
            </div>
        </div>
    );
};
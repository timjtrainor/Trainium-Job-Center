import React from 'react';

interface MarkdownPreviewProps {
    markdown: string;
}

// A simple markdown-to-HTML converter for the expected format from the AI.
const formatMarkdownAsHtml = (text: string): string => {
    if (!text) {
        return '<p class="text-slate-400">Preview will appear here.</p>';
    }

    const inlineFormat = (line: string) => {
        return line
            // Handle bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/__(.*?)__/g, '<strong>$1</strong>')
            // Handle italic text
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/_(.*?)_/g, '<em>$1</em>');
    };

    // Split by 2 or more newlines to create blocks
    const blocks = text.split(/\n\s*\n/);

    const html = blocks.map(block => {
        block = block.trim();
        if (!block) return '';

        // Headings
        if (block.startsWith('### ')) return `<h3>${inlineFormat(block.substring(4))}</h3>`;
        if (block.startsWith('## ')) return `<h2>${inlineFormat(block.substring(3))}</h2>`;
        if (block.startsWith('# ')) return `<h1>${inlineFormat(block.substring(2))}</h1>`;

        // Unordered List
        if (/^[\*\-]\s/.test(block)) {
            const items = block.split('\n').map(item => `<li>${inlineFormat(item.replace(/^[\*\-]\s*/, ''))}</li>`).join('');
            return `<ul>${items}</ul>`;
        }

        // Ordered List
        if (/^\d+\.\s/.test(block)) {
            const items = block.split('\n').map(item => `<li>${inlineFormat(item.replace(/^\d+\.\s*/, ''))}</li>`).join('');
            return `<ol>${items}</ol>`;
        }

        // Paragraphs (with internal line breaks)
        return `<p>${inlineFormat(block).replace(/\n/g, '<br />')}</p>`;
    }).join('');

    return html;
};


export const MarkdownPreview = ({ markdown }: MarkdownPreviewProps): React.ReactNode => {
    const html = formatMarkdownAsHtml(markdown);
    return (
        <div 
            className="prose prose-sm dark:prose-invert max-w-none prose-headings:font-bold prose-headings:text-slate-800 dark:prose-headings:text-slate-200 prose-h1:text-lg prose-h2:text-base prose-h3:text-sm prose-ul:list-disc prose-ul:pl-5 prose-ol:list-decimal prose-ol:pl-5 prose-p:my-2 prose-strong:font-bold prose-strong:text-slate-800 dark:prose-strong:text-slate-200"
            dangerouslySetInnerHTML={{ __html: html }} 
        />
    );
};
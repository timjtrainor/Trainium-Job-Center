export const appendUnique = (existing: string, addition: string): string => {
    const trimmedAddition = addition.trim();
    if (!trimmedAddition) {
        return existing;
    }
    if (!existing.trim()) {
        return trimmedAddition;
    }
    if (existing.includes(trimmedAddition)) {
        return existing;
    }
    return `${existing.trimEnd()}\n\n${trimmedAddition}`;
};

export const linesToList = (value: string): string[] =>
    value
        .split('\n')
        .map(item => item.trim())
        .filter(Boolean);

export const listToLines = (list: string[] = []): string => list.join('\n');

export const formatTimestamp = (value?: string): string => {
    if (!value) {
        return 'Never';
    }
    try {
        return new Date(value).toLocaleString();
    } catch (error) {
        return value;
    }
};

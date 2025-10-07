import { ImpactStory, Interview, InterviewStoryDeckEntry, StrategicNarrative } from '../types';

export interface HydratedDeckItem {
    story_id: string;
    order_index: number;
    story: ImpactStory | null;
    custom_notes: NonNullable<InterviewStoryDeckEntry['custom_notes']>;
}

type DeckNotes = NonNullable<InterviewStoryDeckEntry['custom_notes']>;

type SpeakerNoteMap = { [field: string]: string };

const cloneSpeakerNotes = (notes?: { [key: string]: string }): SpeakerNoteMap => {
    if (!notes || typeof notes !== 'object') {
        return {};
    }
    const clone: SpeakerNoteMap = {};
    Object.entries(notes).forEach(([key, value]) => {
        if (typeof value === 'string') {
            clone[key] = value;
        }
    });
    return clone;
};

const cloneDeckNotes = (notes?: InterviewStoryDeckEntry['custom_notes']): DeckNotes => {
    if (!notes || typeof notes !== 'object') {
        return {};
    }
    const clone: DeckNotes = {};
    Object.entries(notes).forEach(([role, roleNotes]) => {
        if (roleNotes && typeof roleNotes === 'object') {
            clone[role] = { ...roleNotes };
        }
    });
    return clone;
};

const ensureDefaultNotes = (notes: DeckNotes, story: ImpactStory | null): DeckNotes => {
    const nextNotes: DeckNotes = { ...notes };
    if (!nextNotes.default) {
        nextNotes.default = story ? cloneSpeakerNotes(story.speaker_notes) : {};
    }
    return nextNotes;
};

export const buildHydratedDeck = (
    interview: Interview,
    narrative?: StrategicNarrative | null
): HydratedDeckItem[] => {
    const narrativeStories = narrative?.impact_stories ?? [];
    const storiesById = new Map<string, ImpactStory>(narrativeStories.map(story => [story.story_id, story]));

    const sourceDeck: InterviewStoryDeckEntry[] = Array.isArray(interview.story_deck) && interview.story_deck.length > 0
        ? interview.story_deck
        : narrativeStories.map((story, index) => ({
            story_id: story.story_id,
            order_index: index,
            custom_notes: { default: cloneSpeakerNotes(story.speaker_notes) },
        }));

    const hydrated = sourceDeck.map((entry, index) => {
        const story = storiesById.get(entry.story_id) ?? null;
        const baseNotes = ensureDefaultNotes(cloneDeckNotes(entry.custom_notes), story);
        return {
            story_id: entry.story_id,
            order_index: Number.isInteger(entry.order_index) ? (entry.order_index as number) : index,
            story,
            custom_notes: baseNotes,
        };
    });

    return hydrated
        .sort((a, b) => a.order_index - b.order_index)
        .map((item, index) => ({ ...item, order_index: index }));
};

const pruneNotes = (notes: DeckNotes): InterviewStoryDeckEntry['custom_notes'] => {
    const cleaned: DeckNotes = {};
    Object.entries(notes).forEach(([role, fields]) => {
        const filtered: SpeakerNoteMap = {};
        Object.entries(fields || {}).forEach(([field, value]) => {
            if (typeof value === 'string') {
                const trimmed = value.trim();
                if (trimmed.length > 0) {
                    filtered[field] = value;
                }
            }
        });
        if (Object.keys(filtered).length > 0) {
            cleaned[role] = filtered;
        }
    });
    return Object.keys(cleaned).length > 0 ? cleaned : undefined;
};

export const serializeDeck = (deck: HydratedDeckItem[]): InterviewStoryDeckEntry[] =>
    deck.map((item, index) => ({
        story_id: item.story_id,
        order_index: index,
        custom_notes: pruneNotes(item.custom_notes),
    }));

export const ensureRoleOnDeck = (
    deck: HydratedDeckItem[],
    role: string,
    sourceRole: string = 'default'
): HydratedDeckItem[] => deck.map(item => {
    if (item.custom_notes[role]) {
        return item;
    }
    const sourceNotes = item.custom_notes[sourceRole] || {};
    return {
        ...item,
        custom_notes: {
            ...item.custom_notes,
            [role]: { ...sourceNotes },
        },
    };
});

export const removeRoleFromDeck = (deck: HydratedDeckItem[], role: string): HydratedDeckItem[] =>
    deck.map(item => {
        if (!item.custom_notes[role] || role === 'default') {
            return item;
        }
        const { [role]: _removed, ...rest } = item.custom_notes;
        return {
            ...item,
            custom_notes: rest,
        };
    });

export const updateDeckOrder = (deck: HydratedDeckItem[], storyId: string, targetId: string): HydratedDeckItem[] => {
    if (storyId === targetId) {
        return deck;
    }
    const current = [...deck].sort((a, b) => a.order_index - b.order_index);
    const fromIndex = current.findIndex(item => item.story_id === storyId);
    const toIndex = current.findIndex(item => item.story_id === targetId);
    if (fromIndex === -1 || toIndex === -1) {
        return deck;
    }
    const updated = [...current];
    const [moved] = updated.splice(fromIndex, 1);
    updated.splice(toIndex, 0, moved);
    return updated.map((item, index) => ({ ...item, order_index: index }));
};

export const upsertDeckStory = (
    deck: HydratedDeckItem[],
    story: ImpactStory,
    position?: number
): HydratedDeckItem[] => {
    if (deck.some(item => item.story_id === story.story_id)) {
        return deck;
    }
    const insertAt = typeof position === 'number' ? Math.max(0, Math.min(deck.length, position)) : deck.length;
    const clone = [...deck];
    clone.splice(insertAt, 0, {
        story_id: story.story_id,
        order_index: insertAt,
        story,
        custom_notes: { default: cloneSpeakerNotes(story.speaker_notes) },
    });
    return clone.map((item, index) => ({ ...item, order_index: index }));
};

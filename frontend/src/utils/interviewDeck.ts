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

const ensureDefaultNotes = (notes: InterviewStoryDeckEntry['custom_notes'], story: ImpactStory | null): DeckNotes => {
    const base = cloneDeckNotes(notes);
    if (!base.default) {
        base.default = story ? cloneSpeakerNotes(story.speaker_notes) : {};
    } else {
        base.default = cloneSpeakerNotes(base.default);
    }
    return base;
};

const sanitizeDeckEntries = (entries: InterviewStoryDeckEntry[] | null | undefined): InterviewStoryDeckEntry[] => {
    if (!Array.isArray(entries)) {
        return [];
    }
    const seen = new Set<string>();
    return entries.filter(entry => {
        if (!entry || typeof entry !== 'object' || !entry.story_id) {
            return false;
        }
        if (seen.has(entry.story_id)) {
            return false;
        }
        seen.add(entry.story_id);
        return true;
    });
};

const reindexDeck = (items: HydratedDeckItem[]): HydratedDeckItem[] =>
    items
        .slice()
        .sort((a, b) => a.order_index - b.order_index)
        .map((item, index) => ({ ...item, order_index: index }));

export const buildHydratedDeck = (
    interview: Interview,
    narrative?: StrategicNarrative | null
): HydratedDeckItem[] => {
    const narrativeStories = narrative?.impact_stories ?? [];
    const storiesById = new Map<string, ImpactStory>(narrativeStories.map(story => [story.story_id, story]));

    const sanitizedDeck = sanitizeDeckEntries(interview.story_deck);

    const hydrated: HydratedDeckItem[] = sanitizedDeck.map((entry, index) => {
        const story = storiesById.get(entry.story_id) ?? null;
        const baseNotes = ensureDefaultNotes(entry.custom_notes, story);
        return {
            story_id: entry.story_id,
            order_index: Number.isInteger(entry.order_index) ? (entry.order_index as number) : index,
            story,
            custom_notes: baseNotes,
        };
    });

    narrativeStories.forEach((story, index) => {
        const hasStory = hydrated.some(item => item.story_id === story.story_id);
        if (!hasStory) {
            hydrated.push({
                story_id: story.story_id,
                order_index: hydrated.length + index,
                story,
                custom_notes: ensureDefaultNotes({ default: cloneSpeakerNotes(story.speaker_notes) }, story),
            });
        }
    });

    return reindexDeck(hydrated);
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
    reindexDeck(deck).map((item, index) => ({
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
    const baseNotes = ensureDefaultNotes(item.custom_notes, item.story);
    const sourceNotes = baseNotes[sourceRole] || baseNotes.default || {};
    return {
        ...item,
        custom_notes: {
            ...baseNotes,
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
    const current = reindexDeck(deck);
    const fromIndex = current.findIndex(item => item.story_id === storyId);
    if (fromIndex === -1) {
        return deck;
    }
    const toIndex = current.findIndex(item => item.story_id === targetId);
    const updated = [...current];
    const [moved] = updated.splice(fromIndex, 1);
    if (!moved) {
        return deck;
    }
    if (toIndex === -1) {
        updated.push(moved);
    } else {
        updated.splice(toIndex, 0, moved);
    }
    return reindexDeck(updated);
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
    const clone = [...reindexDeck(deck)];
    clone.splice(insertAt, 0, {
        story_id: story.story_id,
        order_index: insertAt,
        story,
        custom_notes: ensureDefaultNotes({ default: cloneSpeakerNotes(story.speaker_notes) }, story),
    });
    return reindexDeck(clone);
};

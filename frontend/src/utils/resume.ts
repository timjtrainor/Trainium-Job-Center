import { v4 as uuidv4 } from 'uuid';
import { WorkExperience, ResumeAccomplishment } from '../types';

/**
 * Ensures every accomplishment in the resume has a unique `achievement_id`.
 * Missing or duplicate IDs are replaced with a fresh uuid.
 * Returns the original resume if no changes were necessary to avoid re-renders.
 */
export function ensureUniqueAchievementIds<T extends { work_experience: WorkExperience[] }>(resume: T): T {
  const seen = new Set<string>();
  let changed = false;

  const work_experience = resume.work_experience.map((exp: WorkExperience) => {
    const newAccs = (exp.accomplishments || []).map((acc: ResumeAccomplishment) => {
      let id = acc.achievement_id;
      if (!id || seen.has(id)) {
        id = uuidv4();
        changed = true;
      }
      seen.add(id);
      return id === acc.achievement_id ? acc : { ...acc, achievement_id: id };
    });
    if (newAccs.some((acc, idx) => acc !== exp.accomplishments[idx])) {
      return { ...exp, accomplishments: newAccs } as WorkExperience;
    }
    return exp;
  });

  return changed ? { ...(resume as any), work_experience } : resume;
}

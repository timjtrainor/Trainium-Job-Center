import React, { useState, useMemo, useEffect, useRef } from 'react';
import { JobApplication, Company, Prompt, InterviewCoachingQuestion, StrategicNarrative, StrategicNarrativePayload, Interview, Contact, ImpactStory, StorytellingFormat, StarBody, ScopeBody, WinsBody, SpotlightBody, InterviewStoryDeckEntry } from '../types';
import { LoadingSpinner, MicrophoneIcon, StrategyIcon, SparklesIcon, LightBulbIcon, GripVerticalIcon, CheckIcon } from './IconComponents';
import * as geminiService from '../services/geminiService';
import { HydratedDeckItem, buildHydratedDeck, ensureRoleOnDeck, removeRoleFromDeck, serializeDeck, updateDeckOrder, upsertDeckStory } from '@/utils/interviewDeck';

interface InterviewStudioViewProps {
    applications: JobApplication[];
    companies: Company[];
    contacts: Contact[];
    activeNarrative: StrategicNarrative | null;
    onSaveNarrative: (payload: StrategicNarrativePayload, narrativeId: string) => Promise<void>;
    prompts: Prompt[];
    initialApp?: JobApplication | null;
    onClearInitialApp: () => void;
    onGetReframeSuggestion: (question: string, coreStories: ImpactStory[]) => Promise<string>;
    onDeconstructQuestion: (question: string) => Promise<{ scope: string[], metrics: string[], constraints: string[] }>;
    onSaveInterviewOpening: (interviewId: string, opening: string) => Promise<void>;
    onSaveInterviewDeck: (interviewId: string, deck: InterviewStoryDeckEntry[]) => Promise<void>;
    debugCallbacks?: { before: (p: string) => Promise<void>; after: (r: string) => Promise<void>; };
}

// --- Editable Co-pilot Sidebar Component ---
const STORY_FORMATS: {
    [key in StorytellingFormat]: {
        fields: { id: keyof (StarBody & ScopeBody & WinsBody & SpotlightBody); label: string; }[];
    }
} = {
    STAR: { fields: [{ id: 'situation', label: 'Situation' }, { id: 'task', label: 'Task' }, { id: 'action', label: 'Action' }, { id: 'result', label: 'Result' }] },
    SCOPE: { fields: [{ id: 'situation', label: 'Situation' }, { id: 'complication', label: 'Complication' }, { id: 'opportunity', label: 'Opportunity' }, { id: 'product_thinking', label: 'Product Thinking' }, { id: 'end_result', label: 'End Result' }] },
    WINS: { fields: [{ id: 'situation', label: 'Situation' }, { id: 'what_i_did', label: 'What I Did' }, { id: 'impact', label: 'Impact' }, { id: 'nuance', label: 'Nuance' }] },
    SPOTLIGHT: { fields: [{ id: 'situation', label: 'Situation' }, { id: 'positive_moment_or_goal', label: 'Positive Moment / Goal' }, { id: 'observation_opportunity', label: 'Observation/Opportunity' }, { id: 'task_action', label: 'Task/Action' }, { id: 'learnings_leverage', label: 'Learnings/Leverage' }, { id: 'impact_results', label: 'Impact/Results' }, { id: 'growth_grit', label: 'Growth/Grit' }, { id: 'highlights_key_trait', label: 'Highlights (Key Trait)' }, { id: 'takeaway_tie_in', label: 'Takeaway/Tie-in' }] },
};

const EditableCopilotSidebar = ({ interview, activeNarrative, onSaveOpening, onSaveDeck }: {
  interview: Interview;
  activeNarrative: StrategicNarrative;
  onSaveOpening: (interviewId: string, opening: string) => Promise<void>;
  onSaveDeck: (interviewId: string, deck: InterviewStoryDeckEntry[]) => Promise<void>;
}) => {
  const [opening, setOpening] = useState(interview.strategic_opening || '');
  const [deck, setDeck] = useState<HydratedDeckItem[]>(() => buildHydratedDeck(interview, activeNarrative));
  const [isSavingOpening, setIsSavingOpening] = useState(false);
  const [isSavingDeck, setIsSavingDeck] = useState(false);
  const [openingSuccess, setOpeningSuccess] = useState(false);
  const [deckSuccess, setDeckSuccess] = useState(false);
  const [activeRole, setActiveRole] = useState('default');
  const [newRoleName, setNewRoleName] = useState('');
  const [storyToAdd, setStoryToAdd] = useState('');
  const [draggingStoryId, setDraggingStoryId] = useState<string | null>(null);

  useEffect(() => {
    setOpening(interview.strategic_opening || '');
  }, [interview]);

  useEffect(() => {
    setDeck(buildHydratedDeck(interview, activeNarrative));
  }, [interview, activeNarrative]);

  const availableRoles = useMemo(() => {
    const roles = new Set<string>();
    deck.forEach(item => {
      Object.keys(item.custom_notes).forEach(role => roles.add(role));
    });
    if (roles.size === 0) {
      roles.add('default');
    }
    return Array.from(roles);
  }, [deck]);

  useEffect(() => {
    if (!availableRoles.includes(activeRole)) {
      setActiveRole(availableRoles[0] || 'default');
    }
  }, [availableRoles, activeRole]);

  useEffect(() => {
    if (!activeRole) {
      return;
    }
    setDeck(prev => {
      if (prev.length === 0) {
        return prev;
      }
      const needsRole = prev.some(item => !item.custom_notes[activeRole]);
      return needsRole ? ensureRoleOnDeck(prev, activeRole) : prev;
    });
  }, [activeRole]);

  const availableStories = useMemo(() => {
    const selectedIds = new Set(deck.map(item => item.story_id));
    return (activeNarrative.impact_stories || []).filter(story => !selectedIds.has(story.story_id));
  }, [deck, activeNarrative]);

  const handleSaveOpening = async () => {
    setIsSavingOpening(true);
    setOpeningSuccess(false);
    try {
      await onSaveOpening(interview.interview_id, opening);
      setOpeningSuccess(true);
      setTimeout(() => setOpeningSuccess(false), 2000);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSavingOpening(false);
    }
  };

  const handleSaveDeck = async () => {
    setIsSavingDeck(true);
    setDeckSuccess(false);
    try {
      await onSaveDeck(interview.interview_id, serializeDeck(deck));
      setDeckSuccess(true);
      setTimeout(() => setDeckSuccess(false), 2000);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSavingDeck(false);
    }
  };

  const handleAddRole = () => {
    const trimmed = newRoleName.trim();
    if (!trimmed) {
      return;
    }
    const existingRole = availableRoles.find(role => role.toLowerCase() === trimmed.toLowerCase());
    if (existingRole) {
      setActiveRole(existingRole);
      setNewRoleName('');
      return;
    }
    setDeck(prev => ensureRoleOnDeck(prev, trimmed));
    setActiveRole(trimmed);
    setNewRoleName('');
  };

  const handleRemoveRole = (role: string) => {
    if (role === 'default') {
      return;
    }
    setDeck(prev => removeRoleFromDeck(prev, role));
  };

  const handleNoteChange = (storyId: string, field: string, value: string) => {
    setDeck(prev => prev.map(item => {
      if (item.story_id !== storyId) {
        return item;
      }
      const roleNotes = item.custom_notes[activeRole] || {};
      return {
        ...item,
        custom_notes: {
          ...item.custom_notes,
          [activeRole]: {
            ...roleNotes,
            [field]: value,
          },
        },
      };
    }));
  };

  const handleDragStart = (storyId: string) => {
    setDraggingStoryId(storyId);
  };

  const handleDragEnter = (storyId: string) => {
    if (!draggingStoryId || draggingStoryId === storyId) {
      return;
    }
    setDeck(prev => updateDeckOrder(prev, draggingStoryId, storyId));
  };

  const handleDragEnd = () => {
    setDraggingStoryId(null);
  };

  const handleAddStory = () => {
    if (!storyToAdd) {
      return;
    }
    const story = (activeNarrative.impact_stories || []).find(s => s.story_id === storyToAdd);
    if (!story) {
      return;
    }
    setDeck(prev => upsertDeckStory(prev, story));
    setStoryToAdd('');
  };

  const handleRemoveStory = (storyId: string) => {
    setDeck(prev => prev
      .filter(item => item.story_id !== storyId)
      .map((item, index) => ({ ...item, order_index: index }))
    );
  };

  const renderDeckItem = (item: HydratedDeckItem) => {
    const story = item.story;
    const formatName = (story?.format || 'STAR') as StorytellingFormat;
    const formatInfo = STORY_FORMATS[formatName];
    const defaultNotes = item.custom_notes.default || {};
    const roleNotes = item.custom_notes[activeRole] || {};

    const dragHandlers = {
      draggable: true,
      onDragStart: (event: React.DragEvent<HTMLDivElement>) => {
        event.dataTransfer.effectAllowed = 'move';
        handleDragStart(item.story_id);
      },
      onDragOver: (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        handleDragEnter(item.story_id);
      },
      onDrop: (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        handleDragEnd();
      },
      onDragEnd: () => handleDragEnd(),
    };

    return (
      <div key={item.story_id} className="p-3 rounded-md bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 space-y-3" {...dragHandlers}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-slate-400 cursor-grab" aria-hidden="true">
              <GripVerticalIcon className="w-4 h-4" />
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{story ? story.story_title : 'Story unavailable'}</p>
              <span className="inline-flex text-xs font-mono px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200">{formatName}</span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => handleRemoveStory(item.story_id)}
            className="text-xs font-semibold text-red-600 hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500 rounded"
          >
            Remove
          </button>
        </div>
        {story ? (
          <div className="space-y-2">
            {(formatInfo?.fields || []).map(field => {
              const fieldName = field.id as string;
              const placeholder = defaultNotes[fieldName] || '';
              const value = roleNotes[fieldName] || '';
              return (
                <div key={fieldName}>
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">{field.label}</label>
                  <textarea
                    rows={2}
                    value={value}
                    placeholder={placeholder}
                    onChange={(e) => handleNoteChange(item.story_id, fieldName, e.target.value)}
                    className="w-full mt-1 p-1 text-xs font-mono bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  {activeRole !== 'default' && placeholder && (
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">Default: {placeholder}</p>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-amber-600">This story is no longer part of the strategic narrative. Add it back or remove it from the deck.</p>
        )}
      </div>
    );
  };

  return (
    <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4 border border-slate-200 dark:border-slate-700 h-full flex flex-col">
      <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 mb-4">Co-pilot Editor</h3>
      <div className="flex-grow overflow-y-auto space-y-4 pr-2">
        <div>
          <div className="flex justify-between items-center">
            <label className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Strategic Opening</label>
            <button onClick={handleSaveOpening} disabled={isSavingOpening} className="inline-flex items-center justify-center w-24 text-xs font-semibold rounded-md shadow-sm transition-colors bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-2 py-1">
              {isSavingOpening ? <LoadingSpinner/> : openingSuccess ? <CheckIcon className="h-4 w-4"/> : 'Save'}
            </button>
          </div>
          <textarea
            value={opening}
            onChange={(e) => setOpening(e.target.value)}
            rows={4}
            className="w-full mt-1 p-2 text-sm text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md"
          />
        </div>
        <div>
          <div className="flex justify-between items-center">
            <label className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Impact Story Deck</label>
            <button onClick={handleSaveDeck} disabled={isSavingDeck} className="inline-flex items-center justify-center w-24 text-xs font-semibold rounded-md shadow-sm transition-colors bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-2 py-1">
              {isSavingDeck ? <LoadingSpinner/> : deckSuccess ? <CheckIcon className="h-4 w-4"/> : 'Save Deck'}
            </button>
          </div>
          <div className="mt-2 space-y-2">
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Persona</span>
                <select
                  value={activeRole}
                  onChange={(e) => setActiveRole(e.target.value)}
                  className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-xs px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {availableRoles.map(role => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
                {activeRole !== 'default' && (
                  <button
                    type="button"
                    onClick={() => handleRemoveRole(activeRole)}
                    className="inline-flex items-center rounded-md border border-slate-300 dark:border-slate-600 px-2 py-1 text-[10px] font-semibold text-red-600 dark:text-red-300 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500"
                  >
                    Remove Role
                  </button>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <input
                  type="text"
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  placeholder="Add interviewer persona"
                  className="w-48 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  type="button"
                  onClick={handleAddRole}
                  disabled={!newRoleName.trim()}
                  className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:bg-indigo-300"
                >
                  Add Role
                </button>
              </div>
              {availableStories.length > 0 && (
                <div className="flex flex-wrap items-center gap-2">
                  <select
                    value={storyToAdd}
                    onChange={(e) => setStoryToAdd(e.target.value)}
                    className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-xs px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Add narrative story…</option>
                    {availableStories.map(story => (
                      <option key={story.story_id} value={story.story_id}>{story.story_title}</option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleAddStory}
                    disabled={!storyToAdd}
                    className="inline-flex items-center rounded-md bg-green-600 px-3 py-1 text-xs font-semibold text-white shadow-sm hover:bg-green-700 disabled:bg-green-300"
                  >
                    Add Story
                  </button>
                </div>
              )}
            </div>
            <div className="space-y-3 mt-1">
              {deck.length > 0 ? deck.map(renderDeckItem) : (
                <p className="text-xs text-slate-500 dark:text-slate-400 text-center">No impact stories available.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- Main Interview Studio Component ---
const useSpeechRecognition = (onResult: (transcript: string) => void) => {
    const recognitionRef = useRef<any>(null);
    const [isRecording, setIsRecording] = useState(false);
    const finalTranscriptRef = useRef(''); // Use a ref to accumulate the final transcript

    useEffect(() => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Speech Recognition API not supported by this browser.");
            return;
        }
        
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                const transcriptPart = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscriptRef.current += transcriptPart + ' ';
                } else {
                    interimTranscript += transcriptPart;
                }
            }
            onResult(finalTranscriptRef.current + interimTranscript);
        };
        
        recognition.onend = () => {
            setIsRecording(false);
            // Clean up any lingering interim transcript when recognition ends.
            onResult(finalTranscriptRef.current);
        };

        recognitionRef.current = recognition;

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
        };
    }, [onResult]);
    
    const startRecording = () => {
        if (recognitionRef.current && !isRecording) {
            finalTranscriptRef.current = ''; // Reset transcript on new recording start
            onResult('');
            recognitionRef.current.start();
            setIsRecording(true);
        }
    };
    
    const stopRecording = () => {
        if (recognitionRef.current && isRecording) {
            recognitionRef.current.stop();
            setIsRecording(false); // onend will also fire and do this, but this is immediate.
        }
    };

    const resetTranscript = () => {
        finalTranscriptRef.current = '';
        onResult('');
    };

    return { isRecording, startRecording, stopRecording, resetTranscript };
};

type PracticePhase =
    | 'idle'
    | 'generating_questions'
    | 'clarifying' // User is prompted to ask clarifying questions
    | 'analyzing_clarification'
    | 'clarification_feedback' // Displaying feedback on their questions
    | 'answering' // User is recording their final answer
    | 'analyzing_answer'
    | 'answer_feedback'; // Displaying feedback on their final answer

export const InterviewStudioView = ({ applications, companies, contacts, activeNarrative, onSaveNarrative, prompts, initialApp, onClearInitialApp, onGetReframeSuggestion, onDeconstructQuestion, onSaveInterviewOpening, onSaveInterviewDeck, debugCallbacks }: InterviewStudioViewProps): React.ReactNode => {
    const [selectedApp, setSelectedApp] = useState<JobApplication | null>(null);
    const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null);
    const [questions, setQuestions] = useState<InterviewCoachingQuestion[]>([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [practiceState, setPracticeState] = useState<PracticePhase>('idle');
    
    const [clarifyingTranscript, setClarifyingTranscript] = useState('');
    const [answerTranscript, setAnswerTranscript] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const [error, setError] = useState<string | null>(null);

    const companyMap = useMemo(() => new Map(companies.map(c => [c.company_id, c.company_name])), [companies]);
    
    const clarifyingMic = useSpeechRecognition(setClarifyingTranscript);
    const answerMic = useSpeechRecognition(setAnswerTranscript);

    const interviewableApps = useMemo(() => {
        return applications.filter(app => app.status?.status_name === 'Interviewing');
    }, [applications]);

    useEffect(() => {
        if (initialApp && interviewableApps.some(app => app.job_application_id === initialApp.job_application_id)) {
            setSelectedApp(initialApp);
            if (initialApp.interviews && initialApp.interviews.length > 0) {
                setSelectedInterview(initialApp.interviews[0]);
            }
            onClearInitialApp();
        }
    }, [initialApp, interviewableApps, onClearInitialApp]);

    const resetState = () => {
        setSelectedApp(null);
        setSelectedInterview(null);
        setPracticeState('idle');
        setQuestions([]);
        setCurrentQuestionIndex(0);
        clarifyingMic.resetTranscript();
        answerMic.resetTranscript();
        setError(null);
    };

    const handleSelectApp = (app: JobApplication) => {
        resetState();
        setSelectedApp(app);
        // If there's only one interview, select it automatically.
        if (app.interviews && app.interviews.length > 0) {
            setSelectedInterview(app.interviews[0]);
        }
    };
    
    const handleStartPractice = async () => {
        if (!activeNarrative) {
            setError("Please define your strategy in the Positioning Hub first.");
            return;
        }
        setPracticeState('generating_questions');
        setError(null);
        try {
            const promptId = selectedApp ? 'GENERATE_JOB_SPECIFIC_INTERVIEW_QUESTIONS' : 'GENERATE_GENERIC_INTERVIEW_QUESTIONS';
            const prompt = prompts.find(p => p.id === promptId);
            if (!prompt) throw new Error(`${promptId} prompt not found.`);

            let result: string[];
            if (selectedApp) {
                const interviewerProfiles = (selectedInterview?.interview_contacts || [])
                    .map(ic => contacts.find(c => c.contact_id === ic.contact_id))
                    .filter(Boolean)
                    .map(c => ({ name: `${c!.first_name} ${c!.last_name}`, title: c!.job_title, profile: c!.linkedin_about }));

                result = await geminiService.generateJobSpecificInterviewQuestions({
                    JOB_DESCRIPTION: selectedApp.job_description,
                    COMPANY_NAME: companyMap.get(selectedApp.company_id) || '',
                    JOB_TITLE: selectedApp.job_title,
                    INTERVIEW_TYPE: selectedInterview?.interview_type,
                    INTERVIEWER_PROFILES_JSON: JSON.stringify(interviewerProfiles),
                    STRATEGIC_HYPOTHESIS_JSON: JSON.stringify(selectedInterview?.strategic_plan)
                }, prompt.content, debugCallbacks);
            } else {
                result = await geminiService.generateGenericInterviewQuestions({
                    DESIRED_TITLE: activeNarrative.desired_title,
                    POSITIONING_STATEMENT: activeNarrative.positioning_statement,
                    MASTERY: activeNarrative.signature_capability,
                    IMPACT_STORY_TITLE: activeNarrative.impact_story_title,
                }, prompt.content, debugCallbacks);
            }
            
            setQuestions(result.map(q => ({ question: q, answer: '', feedback: '', score: 0 })));
            setPracticeState('clarifying');
            setCurrentQuestionIndex(0);
            
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to generate interview questions.");
            setPracticeState('idle');
        }
    };
    
    const handleGetClarificationFeedback = async () => {
        if (!clarifyingTranscript.trim()) {
            setError("Please record your clarifying questions first.");
            return;
        }
        setPracticeState('analyzing_clarification');
        setError(null);
        try {
            const prompt = prompts.find(p => p.id === 'ANALYZE_REFINING_QUESTIONS');
            if (!prompt) throw new Error("Refining questions analysis prompt not found.");
            
            const currentQuestion = questions[currentQuestionIndex];
            const result = await geminiService.analyzeRefiningQuestions({
                QUESTION: currentQuestion.question,
                CLARIFYING_QUESTIONS: clarifyingTranscript,
            }, prompt.content, debugCallbacks);

            const updatedQuestions = [...questions];
            updatedQuestions[currentQuestionIndex] = {
                ...currentQuestion,
                clarifying_questions: clarifyingTranscript,
                clarifying_feedback: result.feedback,
                clarifying_score: result.score,
            };
            setQuestions(updatedQuestions);
            setPracticeState('clarification_feedback');
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to analyze clarifying questions.");
            setPracticeState('clarifying');
        }
    };

    const handleGetAnswerFeedback = async () => {
        if (!answerTranscript.trim()) {
            setError("Please record an answer first.");
            return;
        }
        setPracticeState('analyzing_answer');
        setError(null);

        try {
            const currentQuestion = questions[currentQuestionIndex];
            let result;

            if (selectedApp) {
                const prompt = prompts.find(p => p.id === 'ANALYZE_JOB_SPECIFIC_INTERVIEW_ANSWER');
                if (!prompt) throw new Error("Job-specific analysis prompt not found.");
                result = await geminiService.analyzeJobSpecificInterviewAnswer({
                    JOB_DESCRIPTION: selectedApp.job_description,
                    QUESTION: currentQuestion.question,
                    ANSWER: answerTranscript,
                }, prompt.content, debugCallbacks);
            } else {
                const prompt = prompts.find(p => p.id === 'ANALYZE_GENERIC_INTERVIEW_ANSWER');
                if (!prompt || !activeNarrative) throw new Error("Generic analysis prompt or user profile not found.");
                result = await geminiService.analyzeGenericInterviewAnswer({
                    POSITIONING_STATEMENT: activeNarrative.positioning_statement,
                    MASTERY: activeNarrative.signature_capability,
                    QUESTION: currentQuestion.question,
                    ANSWER: answerTranscript,
                }, prompt.content, debugCallbacks);
            }
            
            const updatedQuestions = [...questions];
            updatedQuestions[currentQuestionIndex] = {
                ...currentQuestion,
                answer: answerTranscript,
                feedback: result.feedback,
                score: result.score
            };
            setQuestions(updatedQuestions);
            setPracticeState('answer_feedback');
            
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to analyze answer.");
            setPracticeState('answering');
        }
    };
    
    const handleNextQuestion = () => {
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(prev => prev + 1);
            clarifyingMic.resetTranscript();
            answerMic.resetTranscript();
            setPracticeState('clarifying');
            setError(null);
        } else {
            resetState();
        }
    };
    
    const handleGetReframe = async () => {
        setIsLoading(true);
        try {
            const suggestion = await onGetReframeSuggestion(questions[currentQuestionIndex].question, activeNarrative?.impact_stories || []);
            const updatedQuestions = [...questions];
            updatedQuestions[currentQuestionIndex].reframe_suggestion = suggestion;
            setQuestions(updatedQuestions);
        } catch(e) { console.error(e) } 
        finally { setIsLoading(false); }
    };

    const handleDeconstruct = async () => {
        setIsLoading(true);
        try {
            const result = await onDeconstructQuestion(questions[currentQuestionIndex].question);
            const updatedQuestions = [...questions];
            updatedQuestions[currentQuestionIndex].deconstructed_questions = result;
            setQuestions(updatedQuestions);
        } catch(e) { console.error(e) } 
        finally { setIsLoading(false); }
    };

    const handleReadAloud = (text: string) => {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    };

    const renderPracticeSession = () => {
        const currentQuestionData = questions[currentQuestionIndex];

        return (
            <div className="space-y-4">
                <div className="flex justify-between items-center">
                    <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Question {currentQuestionIndex + 1} of {questions.length}</p>
                    <button onClick={() => handleReadAloud(currentQuestionData.question)} className="text-sm font-semibold text-blue-600 dark:text-blue-400">Read Aloud</button>
                </div>
                <p className="text-xl font-semibold text-slate-800 dark:text-slate-200">{currentQuestionData?.question}</p>

                 {currentQuestionData.reframe_suggestion && (
                    <div className="p-3 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg text-sm text-indigo-700 dark:text-indigo-300">
                        <span className="font-bold text-indigo-800 dark:text-indigo-200">Coach's Tip:</span> {currentQuestionData.reframe_suggestion}
                    </div>
                )}
                
                {currentQuestionData.deconstructed_questions && (
                    <details className="p-3 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                        <summary className="text-sm font-semibold cursor-pointer">View Deconstructed Questions</summary>
                        <div className="mt-2 text-xs space-y-2">
                            <div><p className="font-bold">Scope:</p><ul className="list-disc pl-5">{(currentQuestionData.deconstructed_questions.scope || []).map((q,i) => <li key={i}>{q}</li>)}</ul></div>
                            <div><p className="font-bold">Metrics:</p><ul className="list-disc pl-5">{(currentQuestionData.deconstructed_questions.metrics || []).map((q,i) => <li key={i}>{q}</li>)}</ul></div>
                            <div><p className="font-bold">Constraints:</p><ul className="list-disc pl-5">{(currentQuestionData.deconstructed_questions.constraints || []).map((q,i) => <li key={i}>{q}</li>)}</ul></div>
                        </div>
                    </details>
                )}

                <div className="flex gap-2">
                    <button onClick={handleGetReframe} disabled={isLoading} className="text-xs font-semibold inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-500 disabled:opacity-50">
                        {isLoading ? <LoadingSpinner/> : <SparklesIcon className="h-4 w-4"/>} Get Strategic Angle
                    </button>
                     <button onClick={handleDeconstruct} disabled={isLoading} className="text-xs font-semibold inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-500 disabled:opacity-50">
                        {isLoading ? <LoadingSpinner/> : <LightBulbIcon className="h-4 w-4"/>} Deconstruct
                    </button>
                </div>
                
                {/* --- Phase 1: Clarification --- */}
                {(practiceState === 'clarifying' || practiceState === 'analyzing_clarification') && (
                    <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg space-y-3">
                        <h4 className="font-semibold text-slate-800 dark:text-slate-200">Step 1: Ask Clarifying Questions</h4>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Before answering, what clarifying questions would you ask to deconstruct the problem? Record yourself asking them.</p>
                        <textarea value={clarifyingTranscript} onChange={(e) => setClarifyingTranscript(e.target.value)} rows={3} className="w-full p-2 rounded-md bg-white dark:bg-slate-700"/>
                        <div className="flex gap-2">
                            <button onClick={clarifyingMic.isRecording ? clarifyingMic.stopRecording : clarifyingMic.startRecording} className={`px-4 py-2 text-sm rounded-md font-semibold text-white ${clarifyingMic.isRecording ? 'bg-red-600' : 'bg-blue-600'}`}><MicrophoneIcon className="h-5 w-5"/></button>
                            <button onClick={handleGetClarificationFeedback} disabled={practiceState === 'analyzing_clarification'} className="px-4 py-2 text-sm rounded-md font-semibold text-white bg-green-600 disabled:bg-green-400">{practiceState === 'analyzing_clarification' ? <LoadingSpinner/> : 'Get Feedback'}</button>
                        </div>
                    </div>
                )}
                
                {/* --- Phase 2: Clarification Feedback & Answer --- */}
                {(practiceState === 'clarification_feedback' || practiceState === 'answering' || practiceState === 'analyzing_answer') && currentQuestionData.clarifying_feedback && (
                    <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-700 space-y-3">
                        <h4 className="font-semibold text-green-800 dark:text-green-200">Clarification Feedback (Score: {currentQuestionData.clarifying_score?.toFixed(1)})</h4>
                        <p className="text-sm text-green-700 dark:text-green-300">{currentQuestionData.clarifying_feedback}</p>
                    </div>
                )}
                
                {(practiceState === 'answering' || practiceState === 'analyzing_answer' || practiceState === 'clarification_feedback') && (
                     <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg space-y-3">
                        <h4 className="font-semibold text-slate-800 dark:text-slate-200">Step 2: Record Your Answer</h4>
                        <textarea value={answerTranscript} onChange={(e) => setAnswerTranscript(e.target.value)} rows={5} className="w-full p-2 rounded-md bg-white dark:bg-slate-700"/>
                        <div className="flex gap-2">
                            <button onClick={answerMic.isRecording ? answerMic.stopRecording : answerMic.startRecording} className={`px-4 py-2 text-sm rounded-md font-semibold text-white ${answerMic.isRecording ? 'bg-red-600' : 'bg-blue-600'}`}><MicrophoneIcon className="h-5 w-5"/></button>
                            <button onClick={handleGetAnswerFeedback} disabled={practiceState === 'analyzing_answer'} className="px-4 py-2 text-sm rounded-md font-semibold text-white bg-green-600 disabled:bg-green-400">{practiceState === 'analyzing_answer' ? <LoadingSpinner/> : 'Get Feedback'}</button>
                        </div>
                    </div>
                )}

                {/* --- Phase 3: Answer Feedback & Next --- */}
                {practiceState === 'answer_feedback' && currentQuestionData.feedback && (
                     <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-700 space-y-3">
                        <h4 className="font-semibold text-green-800 dark:text-green-200">Answer Feedback (Score: {currentQuestionData.score.toFixed(1)})</h4>
                        <p className="text-sm text-green-700 dark:text-green-300">{currentQuestionData.feedback}</p>
                         <button onClick={handleNextQuestion} className="px-4 py-2 text-sm rounded-md font-semibold text-white bg-blue-600">
                           {currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'Finish Session'}
                         </button>
                    </div>
                )}
            </div>
        );
    };

    if (practiceState !== 'idle' && practiceState !== 'generating_questions') {
        return (
            <div className="space-y-6 animate-fade-in h-full flex flex-col">
                <header className="mb-6 flex justify-between items-start flex-shrink-0">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Interview Studio</h1>
                        <p className="mt-1 text-slate-600 dark:text-slate-400">{selectedApp ? `Practicing for ${selectedApp.job_title}` : "Generic Practice"}</p>
                    </div>
                     <div className="flex items-center gap-2">
                        <button onClick={resetState} className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline">
                            End Practice Session
                        </button>
                    </div>
                </header>
                 <div className="flex gap-6 flex-grow min-h-0">
                    <div className="flex-grow bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700 overflow-y-auto">
                        {error && <div className="bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300 p-4 rounded-lg my-6" role="alert">{error}</div>}
                        {renderPracticeSession()}
                    </div>
                    {selectedInterview && activeNarrative && onSaveInterviewDeck && onSaveInterviewOpening && (
                        <div className="w-full max-w-sm flex-shrink-0">
                             <EditableCopilotSidebar
                                interview={selectedInterview}
                                activeNarrative={activeNarrative}
                                onSaveOpening={onSaveInterviewOpening}
                                onSaveDeck={onSaveInterviewDeck}
                            />
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // Setup screen
    return (
        <div className="space-y-6 animate-fade-in">
            <header className="mb-6 flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Interview Studio</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Practice your interview skills with an AI coach.</p>
                </div>
            </header>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 sm:p-8 border border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Practice Mode</h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Choose a specific interview to practice for, or start a generic session based on your active narrative.</p>

                <div className="mt-6 space-y-4">
                    <div>
                        <label htmlFor="app-select" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Practice for a Specific Application (Optional)</label>
                        <select
                            id="app-select"
                            value={selectedApp?.job_application_id || ''}
                            onChange={(e) => {
                                const app = interviewableApps.find(a => a.job_application_id === e.target.value) || null;
                                if(app) handleSelectApp(app); else resetState();
                            }}
                            className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        >
                             <option value="">-- Generic Practice Session --</option>
                            {interviewableApps.map(app => (
                                <option key={app.job_application_id} value={app.job_application_id}>
                                    {companyMap.get(app.company_id)} - {app.job_title}
                                </option>
                            ))}
                        </select>
                    </div>
                    {selectedApp && selectedApp.interviews && selectedApp.interviews.length > 0 && (
                        <div>
                            <label htmlFor="interview-select" className="block text-sm font-medium text-slate-700 dark:text-slate-300">Select Interview Stage</label>
                            <select
                                id="interview-select"
                                value={selectedInterview?.interview_id || ''}
                                onChange={(e) => setSelectedInterview(selectedApp?.interviews?.find(i => i.interview_id === e.target.value) || null)}
                                className="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                            >
                                {selectedApp.interviews.map(interview => (
                                    <option key={interview.interview_id} value={interview.interview_id}>
                                        {interview.interview_type} ({interview.interview_date ? new Date(interview.interview_date+'T00:00:00Z').toLocaleDateString() : 'Date TBD'})
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                <div className="mt-8 flex justify-end">
                     <button
                        onClick={handleStartPractice}
                        disabled={practiceState === 'generating_questions'}
                        className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400"
                    >
                        {practiceState === 'generating_questions' ? <LoadingSpinner/> : 'Start Practice'}
                    </button>
                </div>
                 {error && <p className="text-red-500 text-sm mt-4 text-right">{error}</p>}
            </div>
        </div>
    );
};

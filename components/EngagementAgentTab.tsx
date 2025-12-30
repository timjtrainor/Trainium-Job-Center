import React, { useState, useRef, useEffect } from 'react';
import { AgentMessage, AgentAction, Contact, StrategicNarrative, Prompt, ContactPayload } from '../types';
import * as geminiService from '../services/geminiService';
import { LoadingSpinner, SparklesIcon, UsersIcon, PaperAirplaneIcon, PlusIcon, CheckIcon } from './IconComponents';

interface EngagementAgentTabProps {
    onSaveContact: (contactData: Partial<Contact>) => Promise<void>;
    userProfile: any; // UserProfile
    strategicNarratives: StrategicNarrative[];
    activeNarrative: StrategicNarrative | null;
    prompts: Prompt[];
    // Callbacks for actions
    onCreateDraftMessage: (msg: any) => void;
}

export const EngagementAgentTab = (props: EngagementAgentTabProps) => {
    const [messages, setMessages] = useState<AgentMessage[]>([
        {
            id: 'welcome',
            role: 'assistant',
            content: "Hi! I'm your Engagement Agent. I can help you build your network. Paste a LinkedIn profile to auto-save a contact, or ask me for strategic advice.",
            timestamp: new Date()
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim()) return;

        const userMsg: AgentMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsTyping(true);

        try {
            const systemPrompt = props.prompts.find(p => p.id === 'ENGAGEMENT_AGENT_SYSTEM_PROMPT')?.content || '';
            const narrativeSummary = props.activeNarrative
                ? `${props.activeNarrative.positioning_statement} Mastery: ${props.activeNarrative.signature_capability}`
                : 'No active narrative selected.';

            const context = {
                NORTH_STAR: props.activeNarrative?.positioning_statement,
                MASTERY: props.activeNarrative?.signature_capability,
                NARRATIVE_SUMMARY: narrativeSummary
            };

            const response = await geminiService.runEngagementAgent(
                systemPrompt,
                messages, // History excluding the new message (service adds it? No, service expects history + new msg logic usually, but let's check service impl)
                userMsg.content,
                context
            );

            const assistantMsg: AgentMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.content || "I processed that, but have no specific reply.",
                action: response.action,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMsg]);

        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: "Sorry, I encountered an error providing a response.",
                timestamp: new Date()
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // --- Action Card Handlers ---

    const handleExecuteAction = async (action: AgentAction) => {
        if (action.type === 'CREATE_CONTACT') {
            await props.onSaveContact(action.data);
            // Add a system confirmation message locally
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: `✅ Saved contact: ${action.data.first_name} ${action.data.last_name}`,
                timestamp: new Date()
            }]);
        } else if (action.type === 'DRAFT_MESSAGE') {
            // Passing data up to parent to open modal or populate a draft state
            props.onCreateDraftMessage(action.data);
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: `✅ Draft prepared for ${action.data.contact_name}. Check the modal.`,
                timestamp: new Date()
            }]);
        }
    };

    const renderActionCard = (action: AgentAction) => {
        if (action.type === 'CREATE_CONTACT') {
            const contact = action.data;
            return (
                <div className="mt-3 p-4 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex items-start justify-between">
                        <div>
                            <span className="text-xs font-bold text-blue-600 uppercase tracking-wide">New Contact</span>
                            <h4 className="font-bold text-slate-900 dark:text-white mt-1">{contact.first_name} {contact.last_name}</h4>
                            <p className="text-sm text-slate-600 dark:text-slate-400">{contact.job_title} @ {contact.company_name}</p>
                            {contact.linkedin_about && (
                                <p className="text-xs text-slate-500 mt-2 line-clamp-2 italic">"{contact.linkedin_about}"</p>
                            )}
                        </div>
                        <button
                            onClick={() => handleExecuteAction(action)}
                            className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-2"
                            title="Save Contact"
                        >
                            <PlusIcon className="h-5 w-5" />
                        </button>
                    </div>
                </div>
            );
        }
        if (action.type === 'DRAFT_MESSAGE') {
            return (
                <div className="mt-3 p-4 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                    <div className="flex items-start justify-between">
                        <div>
                            <span className="text-xs font-bold text-purple-600 uppercase tracking-wide">Draft Message</span>
                            <h4 className="font-bold text-slate-900 dark:text-white mt-1">To: {action.data.contact_name}</h4>
                            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 whitespace-pre-wrap border-l-2 border-purple-200 pl-2">{action.data.draft_text}</p>
                        </div>
                        <button
                            onClick={() => handleExecuteAction(action)}
                            className="bg-purple-600 hover:bg-purple-700 text-white rounded-full p-2"
                            title="Use Draft"
                        >
                            <PaperAirplaneIcon className="h-5 w-4" />
                        </button>
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="flex flex-col h-[600px] bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            {/* Header */}
            <div className="bg-white dark:bg-slate-800 p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 dark:bg-blue-900 p-2 rounded-lg">
                        <SparklesIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-slate-900 dark:text-white">Engagement Agent</h3>
                        <p className="text-xs text-slate-500 dark:text-slate-400">AI-powered networking assistant</p>
                    </div>
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`flex max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start gap-3`}>
                            <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-slate-200 dark:bg-slate-700' : 'bg-blue-100 dark:bg-blue-900'}`}>
                                {msg.role === 'user' ? (
                                    <UsersIcon className="h-5 w-5 text-slate-600 dark:text-slate-300" />
                                ) : (
                                    <SparklesIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                                )}
                            </div>
                            <div>
                                <div className={`p-3 rounded-lg text-sm ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-none'
                                    : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 rounded-tl-none'
                                    }`}>
                                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                                </div>

                                {/* Render Action Card if present */}
                                {msg.action && renderActionCard(msg.action)}
                            </div>
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="flex justify-start">
                        <div className="flex max-w-[80%] flex-row items-start gap-3">
                            <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                <SparklesIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div className="bg-white dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700 rounded-tl-none">
                                <LoadingSpinner />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
                <div className="relative">
                    <textarea
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Paste a LinkedIn profile, or ask for strategy advice..."
                        className="w-full pl-4 pr-12 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none h-[60px] max-h-[120px]"
                    />
                    <button
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isTyping}
                        className="absolute right-2 top-2 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition-colors"
                    >
                        <PaperAirplaneIcon className="h-5 w-5" />
                    </button>
                </div>
                <p className="text-xs text-slate-400 mt-2 text-center">
                    Tip: Copy & paste text from any website to smart-extract contacts.
                </p>
            </div>
        </div>
    );
};

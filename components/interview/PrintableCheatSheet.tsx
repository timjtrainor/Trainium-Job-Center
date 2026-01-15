import React from 'react';
import {
    InterviewLensSetup, TMAYConfig, PersonaDefinition, StrategicNarrative
} from '../../types';

interface PrintableCheatSheetProps {
    setup: InterviewLensSetup;
    tmay: TMAYConfig;
    persona: PersonaDefinition;
    activeNarrative?: StrategicNarrative | null;
}

export const PrintableCheatSheet: React.FC<PrintableCheatSheetProps> = ({
    setup,
    tmay,
    persona,
    activeNarrative,
}) => {
    return (
        <div className="print-only hidden print:block bg-white text-slate-900 p-12 font-sans leading-tight">
            {/* Header Info */}
            <header className="border-b-8 border-slate-900 pb-6 mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-black uppercase tracking-tighter">Strategic War Room Sheet</h1>
                    <p className="text-xl font-bold text-slate-600">{setup.role_id} — {setup.objective}</p>
                </div>
                <div className="text-right">
                    <p className="text-sm font-black uppercase tracking-widest text-slate-400">Framework: {setup.narrative_style}</p>
                </div>
            </header>

            <div className="space-y-10">
                {/* Persona & Mandate - Full Width Top Bar */}
                <section className="bg-slate-50 border-2 border-slate-200 rounded-3xl p-8">
                    <div className="grid grid-cols-3 gap-12">
                        <div>
                            <span className="text-blue-600 text-[10px] font-black uppercase tracking-[0.2em] mb-2 block">Interviewer Mandate</span>
                            <h2 className="text-3xl font-black text-slate-900 leading-tight uppercase tracking-tighter">
                                {persona.buyer_type}
                            </h2>
                        </div>
                        <div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Win Condition</p>
                            <p className="text-lg font-bold text-slate-800">{persona.win_condition}</p>
                        </div>
                        <div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Mirroring Style</p>
                            <div className="flex flex-wrap gap-2 pt-1">
                                <span className="px-3 py-1 bg-white border border-slate-200 rounded-full text-slate-600 text-[10px] font-black uppercase tracking-widest">
                                    {persona.communication_style || 'Analytical'}
                                </span>
                                {persona.professional_pedigree && (
                                    <span className="px-3 py-1 bg-white border border-slate-200 rounded-full text-emerald-600 text-[10px] font-black uppercase tracking-widest">
                                        {persona.professional_pedigree}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Identity Stack (TMAY) - Full Visibility Stack */}
                <section className="space-y-6 page-break-after-always">
                    <div className="border-b-2 border-slate-100 pb-2">
                        <h2 className="text-xs font-black uppercase tracking-[0.3em] text-slate-400">Tell Me About Yourself (Opening Pitch)</h2>
                    </div>
                    <div className="space-y-4">
                        {[
                            { label: 'The Hook', text: tmay.hook },
                            { label: 'The Bridge', text: tmay.bridge },
                            { label: 'The Pivot', text: tmay.pivot }
                        ].map((item, index) => (
                            <div key={index} className="border-l-4 border-slate-200 pl-6 py-2">
                                <span className="text-[10px] font-black text-blue-600 uppercase tracking-widest block mb-1">{item.label}</span>
                                <p className="text-xl font-bold text-slate-800 leading-snug">
                                    {item.text || '...'}
                                </p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Strategic Proof Matrix - Filtered by Active Narrative */}
                <section className="space-y-6 pt-4">
                    <div className="border-b-2 border-slate-100 pb-2">
                        <h2 className="text-xs font-black uppercase tracking-[0.3em] text-slate-400">Strategic Proof Portfolio (Signal Only)</h2>
                    </div>

                    <div className="grid grid-cols-2 gap-8">
                        {activeNarrative?.impact_stories?.map((story) => (
                            <div key={story.story_id} className="border-2 border-slate-200 rounded-2xl p-6 bg-white shadow-sm break-inside-avoid mb-4">
                                <div className="flex justify-between items-start mb-4">
                                    <h4 className="text-lg font-black text-slate-900 leading-tight pr-4">{story.story_title}</h4>
                                    <div className="text-right">
                                        <span className="text-2xl font-black text-blue-600 tracking-tighter">{story.hero_kpi}</span>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Signal</p>
                                    </div>
                                </div>
                                <ul className="space-y-2">
                                    {story.thinned_bullets?.map((point, idx) => (
                                        <li key={idx} className="text-sm font-bold text-slate-700 flex items-start">
                                            <div className="mt-1.5 mr-3 h-1.5 w-1.5 rounded-full bg-slate-300 flex-shrink-0" />
                                            {point}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </section>
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
        @media print {
          /* Force all parent containers to allow natural flow and visibility */
          html, body, #__next, main, .fixed.inset-0 {
            height: auto !important;
            overflow: visible !important;
            position: static !important;
            display: block !important;
          }

          body * { visibility: hidden; }
          .print-only, .print-only * { 
            visibility: visible;
          }
          
          .print-only { 
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 100% !important;
            height: auto !important;
            display: block !important;
            background: white !important;
          }

          .page-break-after-always {
            page-break-after: always;
            break-after: page;
          }

          .break-inside-avoid {
            page-break-inside: avoid;
            break-inside: avoid;
          }

          @page {
            size: A4;
            margin: 1.5cm;
          }

          h1, h2, h3, h4 {
            page-break-after: avoid;
          }
        }
      `}} />
        </div>
    );
};

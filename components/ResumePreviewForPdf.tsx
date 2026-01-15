
import React, { forwardRef } from 'react';
import { Resume, DateInfo } from '../types';

interface ResumePreviewProps {
    resume: Resume;
}

const formatDate = (date: DateInfo): string => {
    if (!date || !date.month || !date.year) return '';
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    return `${monthNames[date.month - 1]} ${date.year}`;
};

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="mt-4">
        <h2 className="text-lg font-bold border-b-2 border-gray-700 pb-1 mb-2">{title.toUpperCase()}</h2>
        {children}
    </div>
);

export const ResumePreviewForPdf = forwardRef<HTMLDivElement, ResumePreviewProps>(({ resume }, ref) => {
    const { header, summary, work_experience, education, certifications, skills } = resume;

    // Detect V3 Mode: If any work experience entry has thematic_buckets, we treat it as V3.
    const isV3 = work_experience.some(job => job.thematic_buckets && job.thematic_buckets.length > 0);

    const renderMarkdownText = (text: string) => {
        // Simple parser for **bold** text
        const parts = text.split(/(\*\*.*?\*\*)/g);
        return parts.map((part, index) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <span key={index} className="font-bold">{part.slice(2, -2)}</span>;
            }
            return <span key={index}>{part}</span>;
        });
    };

    return (
        <div ref={ref} className="p-8 bg-white text-gray-800 font-['Inter']" style={{ fontFamily: 'Inter, sans-serif' }}>
            {/* --- HEADER (Common) --- */}
            <div className="text-center mb-6">
                <h1 className="text-3xl font-bold tracking-wider uppercase">{header.first_name} {header.last_name}</h1>
                <p className="text-lg font-medium mt-1">{header.job_title}</p>
                <p className="text-xs mt-2 text-gray-600">
                    {[
                        header.city && header.state ? `${header.city}, ${header.state}` : (header.location || ''),
                        header.email,
                        header.phone_number
                    ].filter(Boolean).join(' | ')}
                </p>
                {header.links && header.links.length > 0 && (
                    <p className="text-xs mt-1 text-gray-600">
                        {header.links.map(l => l.replace(/^https?:\/\//, '')).join(' | ')}
                    </p>
                )}
            </div>

            {/* --- SUMMARY (Legacy Only) --- */}
            {!isV3 && (summary.paragraph || summary.bullets.length > 0) && (
                <Section title="Summary">
                    {summary.paragraph && <p className="text-sm leading-relaxed">{summary.paragraph}</p>}
                    {summary.bullets.length > 0 && (
                        <ul className="list-disc list-inside mt-2 space-y-1">
                            {summary.bullets.map((bullet, index) => (
                                <li key={index} className="text-sm leading-relaxed">{bullet}</li>
                            ))}
                        </ul>
                    )}
                </Section>
            )}

            {/* --- WORK EXPERIENCE (V3 & Legacy) --- */}
            {work_experience && work_experience.length > 0 && (
                <Section title="Professional Experience">
                    {work_experience.map((job, index) => (
                        <div key={index} className={index > 0 ? 'mt-4' : ''}>
                            {/* Role Header */}
                            <div className="flex justify-between items-baseline">
                                <h3 className="text-base font-bold">{job.job_title}</h3>
                                <p className="text-sm font-medium">{formatDate(job.start_date)} – {job.is_current ? 'Present' : formatDate(job.end_date)}</p>
                            </div>
                            <div className="flex justify-between items-baseline mb-1">
                                <p className="text-sm font-semibold">{job.company_name}</p>
                                <p className="text-sm italic text-gray-600">{job.location}</p>
                            </div>

                            {/* Role Context (Common) - Italics */}
                            {job.role_context && (
                                <p className="text-sm italic mb-2 leading-snug text-gray-700">{job.role_context}</p>
                            )}

                            {/* V3: Thematic Buckets */}
                            {isV3 && job.thematic_buckets && job.thematic_buckets.length > 0 ? (
                                <div className="space-y-3 mt-2">
                                    {job.thematic_buckets.map((bucket, bIndex) => (
                                        <div key={bIndex}>
                                            <h4 className="text-sm font-bold mb-1">{bucket.bucket_name}</h4>

                                            {/* Removed The Strike (friction_hook) per latest feedback */}
                                            <ul className="list-disc list-outside ml-4 space-y-1">
                                                {bucket.bullets.map((bullet, bullIndex) => (
                                                    <li key={bullIndex} className="text-sm leading-relaxed pl-1">
                                                        {/* User asked to remove bolding of bullets in PDF, typically applies to preview too for parity */}
                                                        {bullet.replace(/\*\*/g, '')}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                /* Legacy: Flat Accomplishments */
                                <ul className="list-disc list-inside mt-1 space-y-1">
                                    {job.accomplishments.map((acc, accIndex) => (
                                        <li key={accIndex} className="text-sm leading-relaxed">{acc.description}</li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    ))}
                </Section>
            )}

            {/* --- EDUCATION & CERTIFICATIONS (Consolidated in V3) --- */}
            {(education.length > 0 || certifications.length > 0) && (
                <Section title="Education">
                    {education.map((edu, index) => (
                        <div key={index} className={index > 0 ? 'mt-2' : ''}>
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm">
                                    <span className="font-bold">{edu.school}</span>, {edu.location}
                                </span>
                            </div>
                            <div className="text-sm">
                                {edu.degree} in {edu.major.join(', ')}
                            </div>
                        </div>
                    ))}

                    {/* V3: Certifications appended at bottom of Education */}
                    {isV3 && certifications.length > 0 && (
                        <div className="mt-2 pt-2 text-sm border-t border-gray-100">
                            <span className="font-bold">Certifications: </span>
                            {certifications.map((cert, i) => (
                                <span key={i}>
                                    {cert.name} ({cert.organization}){i < certifications.length - 1 ? '; ' : ''}
                                </span>
                            ))}
                        </div>
                    )}
                </Section>
            )}

            {/* --- CERTIFICATIONS (Legacy Only - Standalone Section) --- */}
            {!isV3 && certifications && certifications.length > 0 && (
                <Section title="Certifications">
                    {certifications.map((cert, index) => (
                        <div key={index} className={index > 0 ? 'mt-2' : ''}>
                            <div className="flex justify-between items-baseline">
                                <h3 className="text-base font-semibold">{cert.name}</h3>
                                <p className="text-sm">{new Date(cert.issued_date + 'T00:00:00').toLocaleDateString("en-US", { month: 'long', year: 'numeric', timeZone: 'UTC' })}</p>
                            </div>
                            <p className="text-sm italic">{cert.organization}</p>
                        </div>
                    ))}
                </Section>
            )}

            {/* --- SKILLS (Common - but V3 might want to consolidated this too? Request said Remove Skills/Certs sections. 
                Wait, request said "Section 3: Education & Certifications (CONSOLIDATED) - REMOVE the standalone 'Skills' and 'Certifications' sections."
                It didn't explicitly say what to do with Skills content, but usually Carnegie style puts skills in a specific place or integrates them given the "High-Density". 
                However, looking at the JSON example, there is NO skills array in the root. 
                Let's double check the user request.
                "REMOVE the standalone 'Skills' and 'Certifications' sections."
                Okay, so if isV3, we do NOT render the standalone Skills section. 
                Where do skills go? 
                The prompt/JSON doesn't show them. 
                They might be integated into role context or just omitted in favor of "The Strike".
                I will hide Skills section for V3.
                
                Actually, re-reading: "Section 3: Education & Certifications (CONSOLIDATED) ... REMOVE the standalone 'Skills' and 'Certifications' sections."
                So yes, Skills section is gone in V3. 
            --- */}
            {!isV3 && skills && skills.length > 0 && (
                <Section title="Skills">
                    <div className="text-sm leading-relaxed">
                        {skills.map((skill, index) => (
                            <p key={index}>
                                <span className="font-bold">{skill.heading}:</span> {skill.items.join(', ')}
                            </p>
                        ))}
                    </div>
                </Section>
            )}
        </div>
    );
});

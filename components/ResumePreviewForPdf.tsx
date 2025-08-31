
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

    return (
        <div ref={ref} className="p-8 bg-white text-gray-800 font-['Inter']" style={{ fontFamily: 'Inter, sans-serif' }}>
            <div className="text-center">
                <h1 className="text-3xl font-bold tracking-wider">{header.first_name} {header.last_name}</h1>
                <p className="text-xl font-medium mt-1">{header.job_title}</p>
                <p className="text-xs mt-2">
                    {header.city}, {header.state} | {header.email} | {header.phone_number}
                    {header.links && header.links.length > 0 && ` | ${header.links.join(' | ')}`}
                </p>
            </div>

            {(summary.paragraph || summary.bullets.length > 0) && (
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

            {work_experience && work_experience.length > 0 && (
                <Section title="Work Experience">
                    {work_experience.map((job, index) => (
                        <div key={index} className={index > 0 ? 'mt-3' : ''}>
                            <div className="flex justify-between items-baseline">
                                <h3 className="text-base font-bold">{job.company_name}</h3>
                                <p className="text-sm font-medium">{formatDate(job.start_date)} - {job.is_current ? 'Present' : formatDate(job.end_date)}</p>
                            </div>
                            <div className="flex justify-between items-baseline">
                                <p className="text-sm font-semibold italic">{job.job_title}</p>
                                <p className="text-sm">{job.location}</p>
                            </div>
                            <ul className="list-disc list-inside mt-1 space-y-1">
                                {job.accomplishments.map((acc, accIndex) => (
                                    <li key={accIndex} className="text-sm leading-relaxed">{acc.description}</li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </Section>
            )}

            {education && education.length > 0 && (
                <Section title="Education">
                    {education.map((edu, index) => (
                        <div key={index} className={index > 0 ? 'mt-3' : ''}>
                            <div className="flex justify-between items-baseline">
                                <h3 className="text-base font-bold">{edu.school}</h3>
                                <p className="text-sm font-medium">{edu.start_year} - {edu.end_year}</p>
                            </div>
                            <p className="text-sm">{edu.degree} in {edu.major.join(', ')}</p>
                        </div>
                    ))}
                </Section>
            )}

            {certifications && certifications.length > 0 && (
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
            
            {skills && skills.length > 0 && (
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

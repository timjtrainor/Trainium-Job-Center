import { Document, Packer, Paragraph, TextRun, AlignmentType, Tab, TabStopType, ExternalHyperlink, Table } from 'docx';
import jsPDF from 'jspdf';
import { Resume, DateInfo, ResumeAccomplishment, WorkExperience, Education, SkillSection, ResumeHeader } from '../types';

// Helper to format dates
const formatDate = (date: DateInfo | undefined) => {
    if (!date) return '';
    if (!date.year) return '';
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthStr = date.month ? months[date.month - 1] : '';
    return monthStr ? `${monthStr} ${date.year}` : `${date.year}`;
};

export const generatePdf = (resume: Resume, filename: string) => {
    const doc = new jsPDF();
    let yPos = 20;
    const margin = 20;
    const pageWidth = doc.internal.pageSize.getWidth();
    const contentWidth = pageWidth - (margin * 2);

    // Header
    doc.setFontSize(22);
    doc.setFont("helvetica", "bold");
    doc.text(`${resume.header.first_name} ${resume.header.last_name}`, margin, yPos);
    yPos += 10;

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    const contactInfo = [
        resume.header.location,
        resume.header.phone_number,
        resume.header.email,
        ...(resume.header.links || [])
    ].filter(Boolean).join(' | ');
    doc.text(contactInfo, margin, yPos);
    yPos += 15;

    // Summary
    if (resume.summary?.paragraph) {
        doc.setFontSize(12);
        doc.setFont("helvetica", "bold");
        doc.text("PROFESSIONAL SUMMARY", margin, yPos);
        yPos += 7;
        doc.setFontSize(10);
        doc.setFont("helvetica", "normal");
        const splitText = doc.splitTextToSize(resume.summary.paragraph, contentWidth);
        doc.text(splitText, margin, yPos);
        yPos += (splitText.length * 5) + 5;
    }

    // Experience
    doc.setFontSize(12);
    doc.setFont("helvetica", "bold");
    doc.text("EXPERIENCE", margin, yPos);
    yPos += 7;

    resume.work_experience.forEach(job => {
        doc.setFontSize(11);
        doc.setFont("helvetica", "bold");
        doc.text(job.company_name, margin, yPos);
        doc.setFont("helvetica", "normal");
        const dateStr = `${formatDate(job.start_date)} - ${job.is_current ? 'Present' : formatDate(job.end_date)}`;
        doc.text(dateStr, pageWidth - margin - doc.getTextWidth(dateStr), yPos);
        yPos += 5;

        doc.setFont("helvetica", "italic");
        doc.text(job.job_title, margin, yPos);
        doc.text(job.location, pageWidth - margin - doc.getTextWidth(job.location), yPos);
        yPos += 7;

        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        job.accomplishments.forEach(acc => {
            const bullet = `• ${acc.description}`;
            const splitBullet = doc.splitTextToSize(bullet, contentWidth - 5);
            doc.text(splitBullet, margin + 5, yPos);
            yPos += (splitBullet.length * 5);
        });
        yPos += 5;
    });

    // Education
    if (resume.education && resume.education.length > 0) {
        if (yPos > 250) {
            doc.addPage();
            yPos = 20;
        }
        doc.setFontSize(12);
        doc.setFont("helvetica", "bold");
        doc.text("EDUCATION", margin, yPos);
        yPos += 7;

        resume.education.forEach(edu => {
            doc.setFontSize(10);
            doc.setFont("helvetica", "bold");
            doc.text(edu.school, margin, yPos);
            const dateStr = `${edu.start_year} - ${edu.end_year}`;
            doc.setFont("helvetica", "normal");
            doc.text(dateStr, pageWidth - margin - doc.getTextWidth(dateStr), yPos);
            yPos += 5;
            doc.text(`${edu.degree} ${edu.major ? `in ${edu.major.join(', ')}` : ''}`, margin, yPos);
            yPos += 7;
        });
    }

    // Skills
    if (resume.skills && resume.skills.length > 0) {
        if (yPos > 250) {
            doc.addPage();
            yPos = 20;
        }
        doc.setFontSize(12);
        doc.setFont("helvetica", "bold");
        doc.text("SKILLS", margin, yPos);
        yPos += 7;

        resume.skills.forEach(skillGroup => {
            doc.setFontSize(10);
            doc.setFont("helvetica", "bold");
            doc.text(`${skillGroup.heading}: `, margin, yPos);
            const titleWidth = doc.getTextWidth(`${skillGroup.heading}: `);
            doc.setFont("helvetica", "normal");
            doc.text(skillGroup.items.join(', '), margin + titleWidth, yPos);
            yPos += 5;
        });
    }

    doc.save(`${filename}.pdf`);
};

export const generateDocx = (resume: Resume, filename: string) => {
    const doc = new Document({
        sections: [{
            properties: {},
            children: [
                new Paragraph({
                    children: [
                        new TextRun({
                            text: `${resume.header.first_name} ${resume.header.last_name}`,
                            bold: true,
                            size: 48, // 24pt
                        }),
                    ],
                    alignment: AlignmentType.CENTER,
                    spacing: { after: 100 },
                }),
                new Paragraph({
                    children: [
                        new TextRun({
                            text: [
                                resume.header.location,
                                resume.header.phone_number,
                                resume.header.email,
                                ...(resume.header.links || [])
                            ].filter(Boolean).join(' | '),
                            size: 20, // 10pt
                        }),
                    ],
                    alignment: AlignmentType.CENTER,
                    spacing: { after: 400 },
                }),

                // Summary
                ...(resume.summary?.paragraph ? [
                    new Paragraph({
                        text: "PROFESSIONAL SUMMARY",
                        heading: "Heading2",
                        thematicBreak: true,
                        spacing: { before: 200, after: 100 },
                    }),
                    new Paragraph({
                        text: resume.summary.paragraph,
                    }),
                ] : []),

                // Experience
                new Paragraph({
                    text: "EXPERIENCE",
                    heading: "Heading2",
                    thematicBreak: true,
                    spacing: { before: 200, after: 100 },
                }),
                ...resume.work_experience.flatMap(job => [
                    new Paragraph({
                        children: [
                            new TextRun({
                                text: job.company_name,
                                bold: true,
                                size: 22,
                            }),
                            new TextRun({
                                text: `\t${formatDate(job.start_date)} - ${job.is_current ? 'Present' : formatDate(job.end_date)}`,
                            }),
                        ],
                        tabStops: [
                            {
                                type: TabStopType.RIGHT,
                                position: 9000, // Adjust based on page width
                            },
                        ],
                    }),
                    new Paragraph({
                        children: [
                            new TextRun({
                                text: job.job_title,
                                italics: true,
                            }),
                            new TextRun({
                                text: `\t${job.location}`,
                            }),
                        ],
                        tabStops: [
                            {
                                type: TabStopType.RIGHT,
                                position: 9000,
                            },
                        ],
                        spacing: { after: 100 },
                    }),
                    ...job.accomplishments.map(acc => new Paragraph({
                        text: acc.description,
                        bullet: {
                            level: 0,
                        },
                    })),
                    new Paragraph({ text: "" }), // Spacing
                ]),

                // Education
                ...(resume.education && resume.education.length > 0 ? [
                    new Paragraph({
                        text: "EDUCATION",
                        heading: "Heading2",
                        thematicBreak: true,
                        spacing: { before: 200, after: 100 },
                    }),
                    ...resume.education.flatMap(edu => [
                        new Paragraph({
                            children: [
                                new TextRun({
                                    text: edu.school,
                                    bold: true,
                                }),
                                new TextRun({
                                    text: `\t${edu.location}`,
                                }),
                            ],
                            tabStops: [
                                {
                                    type: TabStopType.RIGHT,
                                    position: 9000,
                                },
                            ],
                        }),
                        new Paragraph({
                            children: [
                                new TextRun({
                                    text: `${edu.degree} ${edu.major ? `in ${edu.major.join(', ')}` : ''}`,
                                }),
                                new TextRun({
                                    text: `\t${edu.start_year} - ${edu.end_year}`,
                                }),
                            ],
                            tabStops: [
                                {
                                    type: TabStopType.RIGHT,
                                    position: 9000,
                                },
                            ],
                            spacing: { after: 100 },
                        }),
                    ])
                ] : []),

                // Skills
                ...(resume.skills && resume.skills.length > 0 ? [
                    new Paragraph({
                        text: "SKILLS",
                        heading: "Heading2",
                        thematicBreak: true,
                        spacing: { before: 200, after: 100 },
                    }),
                    ...resume.skills.map(skillGroup => new Paragraph({
                        children: [
                            new TextRun({
                                text: `${skillGroup.heading}: `,
                                bold: true,
                            }),
                            new TextRun({
                                text: skillGroup.items.join(', '),
                            }),
                        ],
                    }))
                ] : []),
            ],
        }],
    });

    Packer.toBlob(doc).then(blob => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${filename}.docx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
};

export const resumeToMarkdown = (resume: Resume): string => {
    let md = `# ${resume.header.first_name} ${resume.header.last_name}\n\n`;

    // Contact Info
    const contact = [
        resume.header.location,
        resume.header.phone_number,
        resume.header.email,
        ...(resume.header.links || [])
    ].filter(Boolean).join(' | ');
    md += `${contact}\n\n`;

    // Summary
    if (resume.summary?.paragraph) {
        md += `## PROFESSIONAL SUMMARY\n\n${resume.summary.paragraph}\n\n`;
    }

    // Experience
    md += `## EXPERIENCE\n\n`;
    resume.work_experience.forEach(job => {
        const dateStr = `${formatDate(job.start_date)} - ${job.is_current ? 'Present' : formatDate(job.end_date)}`;
        md += `### ${job.company_name} | ${job.location}\n`;
        md += `**${job.job_title}** | ${dateStr}\n\n`;

        job.accomplishments.forEach(acc => {
            md += `- ${acc.description}\n`;
        });
        md += `\n`;
    });

    // Education
    if (resume.education && resume.education.length > 0) {
        md += `## EDUCATION\n\n`;
        resume.education.forEach(edu => {
            const dateStr = `${edu.start_year} - ${edu.end_year}`;
            md += `**${edu.school}** | ${edu.location}\n`;
            md += `${edu.degree} ${edu.major ? `in ${edu.major.join(', ')}` : ''} | ${dateStr}\n\n`;
        });
    }

    // Skills
    if (resume.skills && resume.skills.length > 0) {
        md += `## SKILLS\n\n`;
        resume.skills.forEach(skillGroup => {
            md += `**${skillGroup.heading}**: ${skillGroup.items.join(', ')}\n\n`;
        });
    }

    return md;
};

export const normalizeResume = (resume: any): Resume => {
    if (!resume) {
        return {
            header: { first_name: '', last_name: '', job_title: '', email: '', phone_number: '', city: '', state: '', location: '', links: [] },
            summary: { paragraph: '', bullets: [] },
            work_experience: [],
            education: [],
            certifications: [],
            skills: []
        };
    }

    // Deep copy to avoid mutating original if needed, though here we are restructuring
    const header: ResumeHeader = {
        first_name: resume.header?.first_name || '',
        last_name: resume.header?.last_name || '',
        job_title: resume.header?.job_title || '',
        email: resume.header?.email || '',
        phone_number: resume.header?.phone_number || '',
        city: resume.header?.city || '',
        state: resume.header?.state || '',
        location: resume.header?.location || (resume.header?.city && resume.header?.state ? `${resume.header.city}, ${resume.header.state}` : resume.header?.city || ''),
        links: Array.isArray(resume.header?.links) ? resume.header.links : []
    };

    return {
        header,
        summary: {
            paragraph: resume.summary?.paragraph || '',
            bullets: Array.isArray(resume.summary?.bullets) ? resume.summary.bullets : []
        },
        work_experience: Array.isArray(resume.work_experience) ? resume.work_experience.map((job: any) => ({
            company_name: job.company_name || '',
            job_title: job.job_title || '',
            location: job.location || '',
            start_date: job.start_date || { month: 0, year: 0 },
            end_date: job.end_date || { month: 0, year: 0 },
            is_current: !!job.is_current,
            filter_accomplishment_count: job.filter_accomplishment_count || 3,
            accomplishments: Array.isArray(job.accomplishments) ? job.accomplishments.map((acc: any) => ({
                achievement_id: acc.achievement_id || '',
                description: acc.description || '',
                always_include: !!acc.always_include,
                order_index: acc.order_index || 0,
                // preserve other fields if needed
            })) : []
        })) : [],
        education: Array.isArray(resume.education) ? resume.education : [],
        certifications: Array.isArray(resume.certifications) ? resume.certifications : [],
        skills: Array.isArray(resume.skills) ? resume.skills : []
    };
};

import { Document, Packer, Paragraph, TextRun, AlignmentType, Tab, TabStopType, ExternalHyperlink, Table } from 'docx';
import jsPDF from 'jspdf';
import { Resume, DateInfo, ResumeAccomplishment, WorkExperience, Education, SkillSection, ResumeHeader } from '../types';

// Helper to format dates
const formatDate = (date: DateInfo | undefined, format: 'long' | 'short' = 'long') => {
    if (!date) return '';
    if (!date.year) return '';
    const months = format === 'long'
        ? ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    const monthStr = (date.month && date.month > 0) ? months[date.month - 1] : '';
    return monthStr ? `${monthStr} ${date.year}` : `${date.year}`;
};

export const generatePdf = (resume: Resume, companyName: string) => {
    const doc = new jsPDF('p', 'pt', 'a4');
    const { header, summary, work_experience, education, certifications, skills } = resume;

    const styles = {
        margin: 54,
        colors: {
            text: [31, 41, 55] as [number, number, number],
            accent: [37, 99, 235] as [number, number, number],
            divider: [148, 163, 184] as [number, number, number],
        },
        typography: {
            name: { font: 'helvetica', size: 24, lineHeight: 30 },
            title: { font: 'helvetica', size: 13, lineHeight: 18 },
            contact: { font: 'helvetica', size: 10, lineHeight: 14 },
            section: { font: 'helvetica', size: 11, lineHeight: 16 },
            body: { font: 'helvetica', size: 10.5, lineHeight: 15 },
        },
        spacing: {
            afterName: 8,
            afterTitle: 4,
            afterContact: 2,
            afterLinks: 12,
            sectionTop: 14,
            sectionBottom: 6,
            bulletIndent: 12,
            bulletMarkerOffset: 4,
            jobSpacing: 14,
            jobMetaSpacing: 10,
            betweenColumns: 16,
        },
    } as const;

    type PdfFontWeight = 'normal' | 'bold' | 'italic' | 'bolditalic';

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const contentWidth = pageWidth - styles.margin * 2;
    const bodyLineHeight = styles.typography.body.lineHeight;
    const bulletIndent = styles.spacing.bulletIndent;
    const bulletMarkerOffset = styles.spacing.bulletMarkerOffset;

    doc.setTextColor(...styles.colors.text);
    doc.setLineHeightFactor(1.4);

    let cursorY = styles.margin;

    const setFont = (style: { font: string; size: number }, weight: PdfFontWeight = 'normal') => {
        doc.setFont(style.font, weight).setFontSize(style.size);
    };

    const setBodyFont = (weight: PdfFontWeight = 'normal') => {
        setFont(styles.typography.body, weight);
    };

    const addSpacing = (amount: number) => {
        cursorY += amount;
    };

    const checkPageBreak = (heightNeeded: number = bodyLineHeight) => {
        if (cursorY + heightNeeded > pageHeight - styles.margin) {
            doc.addPage();
            cursorY = styles.margin;
            return true;
        }
        return false;
    };

    const drawSectionHeading = (title: string) => {
        addSpacing(styles.spacing.sectionTop);
        checkPageBreak(styles.typography.section.lineHeight + styles.spacing.sectionBottom + 5);

        setFont(styles.typography.section, 'bold');
        doc.text(title, styles.margin, cursorY);
        addSpacing(styles.spacing.sectionBottom);

        doc.setDrawColor(...styles.colors.divider);
        doc.setLineWidth(0.5);
        doc.line(styles.margin, cursorY, pageWidth - styles.margin, cursorY);
        addSpacing(styles.typography.section.lineHeight / 2 + 2);
    };

    // --- HEADER ---
    setFont(styles.typography.name, 'bold');
    doc.text(`${header.first_name || ''} ${header.last_name || ''}`, pageWidth / 2, cursorY, { align: 'center' });
    addSpacing(styles.typography.name.lineHeight);

    if (header.job_title) {
        setFont(styles.typography.title, 'normal');
        doc.text(header.job_title, pageWidth / 2, cursorY, { align: 'center' });
        addSpacing(styles.typography.title.lineHeight + styles.spacing.afterTitle);
    }

    setFont(styles.typography.contact, 'normal');
    const contactParts = [header.email, header.phone_number, [header.city, header.state].filter(Boolean).join(', ')].filter(Boolean);
    const contactText = contactParts.join('  •  ');
    doc.text(contactText, pageWidth / 2, cursorY, { align: 'center' });
    addSpacing(styles.typography.contact.lineHeight + styles.spacing.afterContact);

    if (header.links && header.links.length > 0) {
        const linksText = header.links.map(l => l.replace(/^https?:\/\//, '')).join('  |  ');
        doc.text(linksText, pageWidth / 2, cursorY, { align: 'center' });
        addSpacing(styles.typography.contact.lineHeight + styles.spacing.afterLinks);
    }

    // --- V3/V4+ DETECTION ---
    const hasThematicBuckets = work_experience.some(job => job.thematic_buckets && job.thematic_buckets.length > 0);
    const hasBillboardAccomplishments = work_experience.some(job => job.accomplishments && job.accomplishments.some(acc => acc.bucket_category));
    const isV3OrHigher = (resume.version && resume.version >= 3.0) || hasThematicBuckets || hasBillboardAccomplishments;

    // --- SUMMARY ---
    const summaryHeadline = summary?.headline;
    const summaryParagraph = summary?.paragraph;
    const summaryBullets = summary?.bullets || [];

    if (summaryHeadline || summaryParagraph || summaryBullets.length > 0) {
        if (summaryHeadline) {
            drawSectionHeading(summaryHeadline.toUpperCase());
        } else {
            drawSectionHeading('Executive Profile');
        }

        if (summaryParagraph) {
            setBodyFont();
            const paragraphLines = doc.splitTextToSize(summaryParagraph, contentWidth);
            const blockHeight = Math.max(paragraphLines.length, 1) * bodyLineHeight;
            checkPageBreak(blockHeight);
            doc.text(paragraphLines, styles.margin, cursorY);
            addSpacing(blockHeight);
        }

        if (summaryBullets.length > 0) {
            const bulletText = summaryBullets.join('  •  ');
            const bulletLines = doc.splitTextToSize(bulletText, contentWidth);
            const blockHeight = Math.max(bulletLines.length, 1) * bodyLineHeight;
            checkPageBreak(blockHeight);
            setBodyFont();
            doc.text(bulletLines, pageWidth / 2, cursorY, { align: 'center' });
            addSpacing(blockHeight + 8);
        }
    }

    // --- EXPERIENCE ---
    if (work_experience.length > 0) {
        drawSectionHeading('Professional Experience');

        work_experience.forEach((job, index) => {
            const companyLine = [job.company_name, job.location].filter(Boolean).join(', ');
            const startText = job.start_date ? formatDate(job.start_date, 'short') : '';
            const endText = job.is_current ? 'Present' : (job.end_date ? formatDate(job.end_date, 'short') : '');
            const dateRange = [startText, endText].filter(Boolean).join(' - ');

            let jobBlockHeight = bodyLineHeight * 2;
            if (job.job_title) jobBlockHeight += bodyLineHeight;
            if (job.role_context) jobBlockHeight += 20;

            if (isV3OrHigher && job.thematic_buckets && job.thematic_buckets.length > 0) {
                job.thematic_buckets.forEach(bucket => {
                    jobBlockHeight += bodyLineHeight + 4;
                    bucket.bullets.forEach(bull => {
                        const lines = doc.splitTextToSize(bull.replace(/\*\*/g, ''), contentWidth - bulletIndent);
                        jobBlockHeight += lines.length * bodyLineHeight;
                    });
                });
            } else {
                job.accomplishments.forEach(acc => {
                    let fullText = acc.description || '';
                    if (acc.bucket_category) {
                        fullText = `${acc.bucket_category}. ${fullText}`;
                    }
                    const lines = doc.splitTextToSize(fullText, contentWidth - bulletIndent);
                    jobBlockHeight += Math.max(lines.length, 1) * bodyLineHeight;
                });
            }
            jobBlockHeight += styles.spacing.jobSpacing;

            checkPageBreak(jobBlockHeight);

            setBodyFont('bold');
            if (companyLine) {
                doc.text(companyLine, styles.margin, cursorY);
            }
            if (dateRange) {
                doc.text(dateRange, pageWidth - styles.margin, cursorY, { align: 'right' });
            }
            addSpacing(bodyLineHeight);

            if (job.job_title) {
                setBodyFont('bold');
                doc.text(job.job_title.toUpperCase(), styles.margin, cursorY);
                addSpacing(bodyLineHeight);
            }

            if (job.role_context) {
                setBodyFont('italic');
                const contextLines = doc.splitTextToSize(job.role_context, contentWidth);
                doc.text(contextLines, styles.margin, cursorY);
                addSpacing(contextLines.length * bodyLineHeight + 6);
            }

            setBodyFont();

            if (isV3OrHigher && job.thematic_buckets && job.thematic_buckets.length > 0) {
                job.thematic_buckets.forEach(bucket => {
                    checkPageBreak(bodyLineHeight + 10);
                    setBodyFont('bold');
                    doc.text(bucket.bucket_name, styles.margin, cursorY);
                    addSpacing(bodyLineHeight + 4);

                    setBodyFont();
                    bucket.bullets.forEach(bullet => {
                        const description = bullet.trim();
                        if (!description) return;

                        const textWithoutMarkdown = description.replace(/\*\*/g, '');
                        const lines = doc.splitTextToSize(textWithoutMarkdown, contentWidth - bulletIndent);
                        const blockHeight = lines.length * bodyLineHeight;

                        checkPageBreak(blockHeight);
                        doc.text('•', styles.margin + bulletMarkerOffset, cursorY);
                        doc.text(lines, styles.margin + bulletIndent, cursorY);
                        addSpacing(blockHeight);
                    });
                    addSpacing(4);
                });
            } else if (job.accomplishments && job.accomplishments.length > 0) {
                job.accomplishments.forEach(acc => {
                    const description = acc.description?.trim();
                    const category = acc.bucket_category?.trim();
                    if (!description) return;

                    if (category) {
                        // Billboard Style: Bold Category. Description
                        setBodyFont('bold');
                        const prefix = `${category}. `;
                        const prefixWidth = doc.getTextWidth(prefix);

                        doc.text('•', styles.margin + bulletMarkerOffset, cursorY);
                        doc.text(prefix, styles.margin + bulletIndent, cursorY);

                        setBodyFont('normal');
                        const firstLineRemainingWidth = contentWidth - bulletIndent - prefixWidth;
                        const lines = doc.splitTextToSize(description, contentWidth - bulletIndent);

                        // Simple approximation for mixed font line wrapping
                        // If description is short, it fits on one line
                        // If not, we might need more complex logic. 
                        // For now, let's keep it simple: draw category, then start description right after it.
                        doc.text(description, styles.margin + bulletIndent + prefixWidth, cursorY, { maxWidth: firstLineRemainingWidth });

                        // Calculate how many lines were used
                        const totalHeight = Math.max(1, doc.splitTextToSize(prefix + description, contentWidth - bulletIndent).length) * bodyLineHeight;
                        addSpacing(totalHeight);
                    } else {
                        const lines = doc.splitTextToSize(description, contentWidth - bulletIndent);
                        const blockHeight = Math.max(lines.length, 1) * bodyLineHeight;

                        checkPageBreak(blockHeight);
                        doc.text('•', styles.margin + bulletMarkerOffset, cursorY);
                        doc.text(lines, styles.margin + bulletIndent, cursorY);
                        addSpacing(blockHeight);
                    }
                });
            }

            if (index < work_experience.length - 1) {
                addSpacing(styles.spacing.jobSpacing);
            }
        });
    }

    // --- EDUCATION & CERTIFICATIONS (Consolidated in V3) ---
    if (education && education.length > 0) {
        drawSectionHeading('Education');

        education.forEach(edu => {
            const degreeText = [edu.degree, (edu.major || []).filter(Boolean).join(', ')].filter(Boolean).join(' in ');
            const schoolLine = [edu.school, edu.location].filter(Boolean).join(', ');
            checkPageBreak(bodyLineHeight * 2);

            if (degreeText) {
                setBodyFont('bold');
                doc.text(degreeText, styles.margin, cursorY);
                addSpacing(bodyLineHeight);
            }

            if (schoolLine) {
                setBodyFont('italic');
                doc.text(schoolLine, styles.margin, cursorY);
                addSpacing(bodyLineHeight);
            }
        });

        if (isV3OrHigher && certifications && certifications.length > 0) {
            checkPageBreak(bodyLineHeight + 4);
            setBodyFont('bold');
            doc.text('Certifications: ', styles.margin, cursorY);
            const labelWidth = doc.getTextWidth('Certifications: ');
            setBodyFont('normal');

            const certText = certifications.map(c => `${c.name} (${c.organization})`).join('; ');
            const lines = doc.splitTextToSize(certText, contentWidth - labelWidth);
            doc.text(lines, styles.margin + labelWidth, cursorY);
            addSpacing(lines.length * bodyLineHeight + 8);
        }
    }

    // --- CERTIFICATIONS ---
    if (!isV3OrHigher && certifications && certifications.length > 0) {
        drawSectionHeading('Certifications');

        certifications.forEach(cert => {
            const certText = `${cert.name}${cert.organization ? ` - ${cert.organization}` : ''}`;
            let dateText = cert.issued_date || '';
            const yearMatch = dateText.match(/\d{4}/);
            if (yearMatch) {
                dateText = yearMatch[0];
            }

            checkPageBreak(bodyLineHeight);

            setBodyFont('bold');
            doc.text(certText, styles.margin, cursorY);

            if (dateText) {
                setBodyFont('normal');
                doc.text(dateText, pageWidth - styles.margin, cursorY, { align: 'right' });
            }

            addSpacing(bodyLineHeight + 2);
        });
    }

    // --- SKILLS (Legacy Only) ---
    if (!isV3OrHigher && skills && skills.length > 0) {
        drawSectionHeading('Skills');

        skills.forEach(skillGroup => {
            const heading = skillGroup.heading ? `${skillGroup.heading}: ` : '';
            const text = heading + (skillGroup.items || []).join(', ');
            const lines = doc.splitTextToSize(text, contentWidth);
            const blockHeight = Math.max(lines.length, 1) * bodyLineHeight;

            checkPageBreak(blockHeight);

            if (skillGroup.heading) {
                setBodyFont('bold');
                doc.text(`${skillGroup.heading}: `, styles.margin, cursorY);
                const headingWidth = doc.getTextWidth(`${skillGroup.heading}: `);
                setBodyFont('normal');
                const remainingText = (skillGroup.items || []).join(', ');
                const wrappedRemaining = doc.splitTextToSize(remainingText, contentWidth - headingWidth);
                doc.text(wrappedRemaining, styles.margin + headingWidth, cursorY);
                addSpacing(blockHeight + 4);
            } else {
                setBodyFont('normal');
                doc.text(lines, styles.margin, cursorY);
                addSpacing(blockHeight + 4);
            }
        });
    }

    const filename = `${header.first_name || 'Resume'} ${header.last_name || ''} - ${header.job_title || 'Role'}${companyName ? ` - ${companyName}` : ''}.pdf`;
    doc.save(filename);
};

export const generateDocx = async (resume: Resume, companyName: string) => {
    const { header, summary, work_experience, education, certifications, skills } = resume;
    const hasThematicBuckets = work_experience.some(job => job.thematic_buckets && job.thematic_buckets.length > 0);
    const hasBillboardAccomplishments = work_experience.some(job => job.accomplishments && job.accomplishments.some(acc => acc.bucket_category));
    const isV3OrHigher = (resume.version && resume.version >= 3.0) || hasThematicBuckets || hasBillboardAccomplishments;

    const parseMarkdown = (text: string) => {
        const parts = text.split(/(\*\*.*?\*\*)/g);
        return parts.map(part => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return new TextRun({ text: part.slice(2, -2), bold: true });
            }
            return new TextRun({ text: part });
        });
    };

    const docChildren: (Paragraph | Table)[] = [
        new Paragraph({ style: "ApplicantName", text: `${header.first_name || ''} ${header.last_name || ''}` }),
        new Paragraph({ style: "JobTitle", text: header.job_title || '' }),
        new Paragraph({
            style: "ContactInfo",
            children: [
                new ExternalHyperlink({
                    children: [new TextRun({ text: header.email || '', style: "ContactInfo" })],
                    link: `mailto:${header.email}`,
                }),
                new TextRun({ text: " | ", style: "ContactInfo" }),
                new ExternalHyperlink({
                    children: [new TextRun({ text: header.phone_number || '', style: "ContactInfo" })],
                    link: `tel:${header.phone_number}`,
                }),
                new TextRun({
                    text: (header.city || header.state) ? ` | ${[header.city, header.state].filter(Boolean).join(', ')}` : '',
                    style: "ContactInfo"
                }),
            ],
            spacing: { after: 0 }
        }),
        new Paragraph({
            style: "ContactInfo",
            children: (header.links || []).flatMap((link, i) => {
                const cleanLink = link.replace(/^https?:\/\//, '');
                const parts: any[] = [
                    new ExternalHyperlink({
                        children: [new TextRun({ text: cleanLink, style: "ContactInfo" })],
                        link: link.startsWith('http') ? link : `https://${link}`,
                    })
                ];
                if (i < (header.links?.length || 0) - 1) {
                    parts.push(new TextRun({ text: " | ", style: "ContactInfo" }));
                }
                return parts;
            })
        }),
    ];

    // --- SUMMARY ---
    if (summary.headline || summary.paragraph || (summary.bullets && summary.bullets.length > 0)) {
        if (summary.headline) {
            docChildren.push(new Paragraph({
                style: "Section",
                text: summary.headline.toUpperCase(),
                alignment: AlignmentType.LEFT,
                thematicBreak: true
            }));
        } else {
            docChildren.push(new Paragraph({ style: "Section", text: "Executive Profile", thematicBreak: true }));
        }

        if (summary.paragraph) {
            docChildren.push(new Paragraph({ text: summary.paragraph, style: "Normal" }));
        }

        if (summary.bullets && summary.bullets.length > 0) {
            docChildren.push(new Paragraph({
                text: summary.bullets.join('  •  '),
                style: "Normal",
                alignment: AlignmentType.CENTER
            }));
        }
    }

    // --- PROFESSIONAL EXPERIENCE ---
    if (work_experience && work_experience.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Professional Experience", thematicBreak: true }));
        work_experience.forEach((exp, index) => {
            const spacingBefore = index === 0 ? 0 : 200;

            docChildren.push(
                new Paragraph({
                    spacing: { before: spacingBefore, after: 0 },
                    keepNext: true,
                    keepLines: true,
                    children: [
                        new TextRun({ text: `${exp.company_name}, ${exp.location}`, bold: true, size: 24, font: "Calibri" }),
                        new TextRun({ children: [new Tab(), `${formatDate(exp.start_date)} - ${exp.is_current ? 'Present' : formatDate(exp.end_date)}`], size: 24, font: "Calibri" }),
                    ],
                    tabStops: [{ type: TabStopType.RIGHT, position: 9600 }],
                }),
                new Paragraph({
                    style: "JobHeading2",
                    children: [new TextRun({ text: exp.job_title.toUpperCase(), bold: true })],
                    keepNext: true,
                    keepLines: true,
                })
            );

            if (exp.role_context) {
                docChildren.push(new Paragraph({
                    style: "JobHeading2",
                    text: exp.role_context,
                    keepNext: true,
                    keepLines: true,
                }));
            }

            if (isV3OrHigher && exp.thematic_buckets && exp.thematic_buckets.length > 0) {
                exp.thematic_buckets.forEach(bucket => {
                    docChildren.push(new Paragraph({
                        text: bucket.bucket_name,
                        style: "Normal",
                        spacing: { before: 0, after: 0 }, // Removed all spacing
                        run: { bold: true }
                    }));

                    bucket.bullets.forEach((bullet, bullIdx) => {
                        docChildren.push(new Paragraph({
                            children: parseMarkdown(bullet),
                            style: "ListParagraph",
                            bullet: { level: 0 },
                            keepLines: true,
                            spacing: { before: 0, after: 0 } // Removed spacing after lists
                        }));
                    });
                });
            } else {
                exp.accomplishments.forEach((acc, i) => {
                    const isLast = i === exp.accomplishments.length - 1;
                    const children: any[] = [];

                    if (acc.bucket_category) {
                        children.push(new TextRun({ text: acc.bucket_category, bold: true }));
                        children.push(new TextRun({ text: ". ", bold: true }));
                        children.push(new TextRun({ text: acc.description }));
                    } else {
                        children.push(new TextRun({ text: acc.description }));
                    }

                    docChildren.push(new Paragraph({
                        children,
                        style: "ListParagraph",
                        bullet: { level: 0 },
                        keepNext: !isLast,
                        keepLines: true,
                        spacing: { after: isLast ? 100 : 0 }
                    }));
                });
            }
        });
    }

    // --- EDUCATION & CERTIFICATIONS (Consolidated in V3) ---
    if (education && education.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Education", thematicBreak: true }));
        education.forEach(edu => {
            docChildren.push(
                new Paragraph({
                    spacing: { after: 40 },
                    children: [
                        new TextRun({ text: `${edu.degree} in ${edu.major.join(', ')}`, bold: true, size: 24, font: "Calibri" }),
                    ],
                    tabStops: [{ type: TabStopType.RIGHT, position: 9600 }],
                }),
                new Paragraph({
                    style: "EduOther",
                    text: `${edu.school}, ${edu.location}`,
                    spacing: { after: 100 }
                })
            );
        });

        if (isV3OrHigher && certifications && certifications.length > 0) {
            docChildren.push(new Paragraph({
                children: [
                    new TextRun({ text: "Certifications: ", bold: true }),
                    new TextRun({ text: certifications.map(c => `${c.name} (${c.organization})`).join('; ') })
                ],
                style: "Normal",
                spacing: { before: 100 }
            }));
        }
    }

    // --- CERTIFICATIONS ---
    if (!isV3OrHigher && certifications && certifications.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Certifications", thematicBreak: true }));
        certifications.forEach(cert => {
            let dateText = cert.issued_date || '';
            const yearMatch = dateText.match(/\d{4}/);
            if (yearMatch) {
                dateText = yearMatch[0];
            }

            docChildren.push(
                new Paragraph({
                    spacing: { after: 0 },
                    children: [
                        new TextRun({ text: cert.name, bold: true, size: 24, font: "Calibri" }),
                        new TextRun({ text: ` - ${cert.organization}`, size: 24, font: "Calibri" }),
                        new TextRun({ children: [new Tab(), dateText], size: 24, font: "Calibri" }),
                    ],
                    tabStops: [{ type: TabStopType.RIGHT, position: 9600 }],
                })
            );
        });
    }

    // --- SKILLS ---
    if (!isV3OrHigher && skills && skills.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Skills", thematicBreak: true }));
        skills.forEach(skillGroup => {
            docChildren.push(new Paragraph({
                children: [
                    new TextRun({ text: `${skillGroup.heading || 'Skills'}: `, bold: true }),
                    new TextRun({ text: (skillGroup.items || []).join(', ') }),
                ],
                style: "SkillCell"
            }));
        });
    }

    const doc = new Document({
        styles: {
            default: {
                document: {
                    run: { font: "Calibri", size: 22 },
                },
            },
            paragraphStyles: [
                { id: "Normal", name: "Normal", run: { font: "Calibri", size: 22 }, paragraph: { spacing: { after: 120 } } },
                { id: "ApplicantName", name: "Applicant Name", basedOn: "Normal", run: { font: "Calibri", size: 48, bold: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 0 } } },
                { id: "JobTitle", name: "Job Title", basedOn: "Normal", run: { font: "Calibri", size: 28 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 0 } } },
                { id: "ContactInfo", name: "Contact Info", basedOn: "Normal", run: { font: "Calibri", size: 22 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 120 } } },
                { id: "Section", name: "Section", basedOn: "Normal", run: { font: "Calibri", size: 24, bold: true, allCaps: true }, paragraph: { spacing: { before: 240, after: 120 } } },
                { id: "JobHeading2", name: "Job Heading 2", basedOn: "Normal", run: { font: "Calibri", size: 22, italics: true }, paragraph: { spacing: { after: 100 } } },
                { id: "EduOther", name: "EduOther", basedOn: "Normal", run: { font: "Calibri", size: 22, italics: true } },
                { id: "ListParagraph", name: "List Paragraph", basedOn: "Normal", paragraph: { indent: { left: 288 }, spacing: { after: 0 } } },
                { id: "SkillCell", name: "Skill Cell", basedOn: "ListParagraph", run: { font: "Calibri", size: 22 }, paragraph: { indent: { left: 200 }, spacing: { after: 40 } } },
            ]
        },
        sections: [{
            properties: {
                page: {
                    margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
                },
            },
            children: docChildren
        }],
    });

    const filename = `${header.first_name || 'Resume'} ${header.last_name || ''} - ${header.job_title || 'Role'}${companyName ? ` - ${companyName}` : ''}.docx`;
    const blob = await Packer.toBlob(doc);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
};

export const resumeToMarkdown = (resume: Resume): string => {
    const hasThematicBuckets = resume.work_experience.some(job => job.thematic_buckets && job.thematic_buckets.length > 0);
    const hasBillboardAccomplishments = resume.work_experience.some(job => job.accomplishments && job.accomplishments.some(acc => acc.bucket_category));
    const isV3OrHigher = (resume.version && resume.version >= 3.0) || hasThematicBuckets || hasBillboardAccomplishments;
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
        md += `**${job.job_title.toUpperCase()}** | ${dateStr}\n\n`;

        if (job.role_context) {
            md += `*${job.role_context}*\n\n`;
        }

        if (isV3OrHigher && job.thematic_buckets && job.thematic_buckets.length > 0) {
            job.thematic_buckets.forEach(bucket => {
                md += `**${bucket.bucket_name}**\n`;
                bucket.bullets.forEach(bullet => {
                    md += `- ${bullet}\n`;
                });
                md += `\n`;
            });
        } else {
            job.accomplishments.forEach(acc => {
                if (acc.bucket_category) {
                    md += `- **${acc.bucket_category}.** ${acc.description}\n`;
                } else {
                    md += `- ${acc.description}\n`;
                }
            });
            md += `\n`;
        }
    });

    // Education & Certifications (Consolidated in V3)
    if (resume.education && resume.education.length > 0) {
        md += `## EDUCATION\n\n`;
        resume.education.forEach(edu => {
            const dateStr = `${edu.start_year || ''} - ${edu.end_year || ''}`;
            md += `**${edu.school}** | ${edu.location}\n`;
            md += `${edu.degree} ${edu.major ? `in ${edu.major.join(', ')}` : ''} | ${dateStr}\n\n`;
        });

        if (isV3OrHigher && resume.certifications && resume.certifications.length > 0) {
            md += `**Certifications**: ${resume.certifications.map(c => `${c.name} (${c.organization})`).join('; ')}\n\n`;
        }
    }

    // Standalone
    if (!isV3OrHigher) {
        if (resume.certifications && resume.certifications.length > 0) {
            md += `## CERTIFICATIONS\n\n`;
            resume.certifications.forEach(cert => {
                let dateText = cert.issued_date || '';
                const yearMatch = dateText.match(/\d{4}/);
                if (yearMatch) dateText = yearMatch[0];
                md += `**${cert.name}** | ${cert.organization}\n`;
                md += `${dateText}\n\n`;
            });
        }

        if (resume.skills && resume.skills.length > 0) {
            md += `## SKILLS\n\n`;
            resume.skills.forEach(skillGroup => {
                md += `**${skillGroup.heading}**: ${skillGroup.items.join(', ')}\n\n`;
            });
        }
    }

    return md;
};

const normalizeDateField = (value: any): DateInfo => {
    if (!value) return { month: 0, year: 0 };
    if (typeof value === 'object' && typeof value.month === 'number' && typeof value.year === 'number') {
        return { month: value.month || 0, year: value.year || 0 };
    }
    if (typeof value === 'string') {
        const trimmed = value.trim();
        const [yearPart, monthPart] = trimmed.split('-');
        const year = parseInt(yearPart, 10);
        const month = monthPart ? parseInt(monthPart, 10) : 0;
        if (!Number.isNaN(year)) {
            return { year, month: (!Number.isNaN(month) && month >= 1 && month <= 12) ? month : 0 };
        }
    }
    return { month: 0, year: 0 };
};

export const normalizeResume = (resume: any, version?: number): Resume => {
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

    // Handle potential wrapped format (resume: { ... })
    const data = resume.resume || resume;

    const header: ResumeHeader = {
        first_name: data.header?.first_name || '',
        last_name: data.header?.last_name || '',
        job_title: data.header?.job_title || '',
        email: data.header?.email || '',
        phone_number: data.header?.phone_number || '',
        city: data.header?.city || '',
        state: data.header?.state || '',
        location: data.header?.location || ([data.header?.city, data.header?.state].filter(Boolean).join(', ')),
        links: Array.isArray(data.header?.links) ? data.header.links : []
    };

    const work_experience: WorkExperience[] = (Array.isArray(data.work_experience) ? data.work_experience : []).map((job: any) => ({
        company_name: job.company_name || '',
        job_title: job.job_title || '',
        location: job.location || '',
        start_date: normalizeDateField(job.start_date),
        end_date: normalizeDateField(job.end_date),
        is_current: !!job.is_current,
        role_context: job.role_context || '',
        filter_accomplishment_count: job.filter_accomplishment_count || 0,
        accomplishments: (Array.isArray(job.accomplishments) ? job.accomplishments : []).map((acc: any) => ({
            achievement_id: acc.achievement_id || '',
            description: acc.description || '',
            bucket_category: acc.bucket_category || '',
            always_include: !!acc.always_include,
            order_index: acc.order_index || 0,
        })),
        thematic_buckets: Array.isArray(job.thematic_buckets) ? job.thematic_buckets.map((bucket: any) => ({
            bucket_name: bucket.bucket_name || '',
            bullets: Array.isArray(bucket.bullets) ? bucket.bullets : [],
            friction_hook: bucket.friction_hook || ''
        })) : undefined
    }));

    // Handle AI workflow education format (nested education array)
    const eduSource = Array.isArray(data.education?.education)
        ? data.education.education
        : (Array.isArray(data.education) ? data.education : []);

    const education: Education[] = eduSource.map((edu: any) => ({
        school: edu.school || '',
        location: edu.location || '',
        degree: edu.degree || '',
        major: Array.isArray(edu.major) ? edu.major : (edu.major ? [edu.major] : []),
        minor: Array.isArray(edu.minor) ? edu.minor : (edu.minor ? [edu.minor] : []),
        start_month: edu.start_month || 0,
        start_year: edu.start_year || 0,
        end_month: edu.end_month || 0,
        end_year: edu.end_year || 0,
    }));

    // Handle AI workflow skills format
    let skills: SkillSection[] = [];
    if (Array.isArray(data.skills)) {
        skills = data.skills;
    } else if (data.skills && typeof data.skills === 'object' && 'items' in data.skills) {
        skills = [{
            heading: data.skills.heading || 'Skills',
            items: data.skills.items || []
        }];
    }

    const certifications = (Array.isArray(data.certifications) ? data.certifications : []).map((cert: any) => ({
        name: cert.name || '',
        organization: cert.organization || '',
        link: cert.link || '',
        issued_date: cert.issued_date || ''
    }));

    return {
        header,
        summary: {
            headline: data.summary?.headline || '',
            paragraph: data.summary?.paragraph || '',
            bullets: Array.isArray(data.summary?.bullets) ? data.summary.bullets : []
        },
        work_experience,
        education,
        certifications,
        skills,
        version: version || data.version
    };
};

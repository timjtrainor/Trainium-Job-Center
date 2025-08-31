import React, { useState } from 'react';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Tab, TabStopType, TabStopPosition, UnderlineType, Table, TableCell, TableRow, WidthType, BorderStyle } from 'docx';
import jsPDF from 'jspdf';
import { Resume, DateInfo } from '../types';
import { LoadingSpinner, DocumentTextIcon, LightBulbIcon, ArrowDownTrayIcon, ClipboardDocumentListIcon, ClipboardDocumentCheckIcon } from './IconComponents';


interface DownloadResumeStepProps {
  finalResume: Resume;
  companyName: string;
  onNext?: () => void;
  onSaveAndStartAnother?: () => void;
  isLoading: boolean;
  onOpenJobDetailsModal?: () => void;
  onOpenAiAnalysisModal?: () => void;
  onClose?: () => void;
}

const formatDate = (date: DateInfo, format: 'short' | 'long' | 'year' = 'long'): string => {
    if (!date || !date.month || !date.year) return '';
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    if (format === 'year') return date.year.toString();
    if (format === 'short') return `${monthNames[date.month - 1].substring(0,3)} ${date.year}`;
    return `${monthNames[date.month - 1]} ${date.year}`;
};

const generateDocx = async (resume: Resume, companyName: string) => {
    const { header, summary, work_experience, education, certifications, skills } = resume;

    const docChildren: (Paragraph | Table)[] = [
        new Paragraph({ style: "ApplicantName", text: `${header.first_name || ''} ${header.last_name || ''}` }),
        new Paragraph({ style: "JobTitle", text: header.job_title || '' }),
        new Paragraph({ style: "ContactInfo", text: `${header.city || ''}, ${header.state || ''} · ${header.email || ''} · ${header.phone_number || ''} · ${(header.links || []).join(' · ')}` }),
    ];

    if (summary.paragraph || (summary.bullets && summary.bullets.length > 0)) {
        docChildren.push(new Paragraph({ style: "Section", text: "Executive Profile" }));
        if (summary.paragraph) {
            docChildren.push(new Paragraph({ text: summary.paragraph, style: "Normal" }));
        }
        if (summary.bullets && summary.bullets.length > 0) {
            summary.bullets.forEach(bullet => docChildren.push(new Paragraph({ text: bullet, style: "ListParagraph", bullet: { level: 0 } })));
        }
    }

    if (skills && skills.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Core Competencies" }));
        const allSkillItems = skills.flatMap(s => s.items);
        const numItemsPerCol = Math.ceil(allSkillItems.length / 3);
        const col1Items = allSkillItems.slice(0, numItemsPerCol);
        const col2Items = allSkillItems.slice(numItemsPerCol, 2 * numItemsPerCol);
        const col3Items = allSkillItems.slice(2 * numItemsPerCol);

        const createCellParagraphs = (items: string[]) => {
            return items.length > 0 ? items.map(item => new Paragraph({ text: item, bullet: { level: 0 }, style: "SkillCell" })) : [new Paragraph('')];
        }

        const skillsTable = new Table({
            columnWidths: [3000, 3000, 3000],
            width: { size: 9000, type: WidthType.DXA },
            borders: {
                top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                insideHorizontal: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                insideVertical: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
            },
            rows: [
                new TableRow({
                    children: [
                        new TableCell({ children: createCellParagraphs(col1Items), margins: { right: 100 } }),
                        new TableCell({ children: createCellParagraphs(col2Items), margins: { right: 100, left: 100 } }),
                        new TableCell({ children: createCellParagraphs(col3Items), margins: { left: 100 } }),
                    ],
                }),
            ],
        });
        docChildren.push(skillsTable);
    }
    
    if (work_experience && work_experience.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Professional Experience" }));
        work_experience.forEach((exp, index) => {
            const spacingBefore = index === 0 ? 0 : 100;

            docChildren.push(
                new Paragraph({
                    spacing: { before: spacingBefore, after: 0 },
                    children: [
                        new TextRun({ text: `${exp.company_name}, ${exp.location}`, bold: true, size: 24, font: "Calibri" }),
                        new TextRun({ children: [new Tab(), `${formatDate(exp.start_date)} - ${exp.is_current ? 'Present' : formatDate(exp.end_date)}`], size: 24, font: "Calibri" }),
                    ],
                    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
                }),
                new Paragraph({ style: "JobHeading2", text: exp.job_title })
            );
            exp.accomplishments.forEach(acc => docChildren.push(new Paragraph({ text: acc.description, style: "ListParagraph", bullet: { level: 0 } })));
        });
    }

    if (education && education.length > 0) {
        docChildren.push(new Paragraph({ style: "Section", text: "Education" }));
        education.forEach(edu => {
            docChildren.push(
                new Paragraph({
                    children: [
                        new TextRun({ text: `${edu.degree} in ${edu.major.join(', ')}`, bold: true, size: 24, font: "Calibri" }),
                        new TextRun({ children: [new Tab(), `${edu.start_year} - ${edu.end_year}`], size: 24, font: "Calibri" }),
                    ],
                    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
                }),
                new Paragraph({ style: "EduOther", text: `${edu.school}, ${edu.location}` })
            );
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
                { id: "ContactInfo", name: "Contact Info", basedOn: "Normal", run: { font: "Calibri", size: 22 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 240 } } },
                { id: "Section", name: "Section", basedOn: "Normal", run: { font: "Georgia", size: 24, bold: true, allCaps: true }, paragraph: { spacing: { before: 240, after: 120 }, border: { bottom: { color: "auto", space: 1, style: "single", size: 6 } } } },
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
    
    const filename = `${header.first_name || 'Resume'} ${header.last_name || ''} - ${resume.header.job_title} - ${companyName}.docx`;
    const blob = await Packer.toBlob(doc);
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
};

const generatePdf = (resume: Resume, companyName: string) => {
    const doc = new jsPDF('p', 'pt', 'a4');
    const { header, summary, work_experience, education, skills } = resume;

    const pageW = doc.internal.pageSize.getWidth();
    const margin = 40;
    let cursorY = margin;

    const checkPageBreak = (heightNeeded: number) => {
        if (cursorY + heightNeeded > doc.internal.pageSize.getHeight() - margin) {
            doc.addPage();
            cursorY = margin;
        }
    };

    // --- Header ---
    doc.setFont('helvetica', 'bold').setFontSize(24).text(`${header.first_name} ${header.last_name}`, pageW / 2, cursorY, { align: 'center' });
    cursorY += 28;
    doc.setFont('helvetica', 'normal').setFontSize(14).text(header.job_title, pageW / 2, cursorY, { align: 'center' });
    cursorY += 18;
    doc.setFontSize(9).text(`${header.city}, ${header.state} | ${header.email} | ${header.phone_number}`, pageW / 2, cursorY, { align: 'center' });
    cursorY += 12;
    if (header.links && header.links.length > 0) {
        doc.setTextColor(63, 131, 248).textWithLink(header.links.join(' | '), pageW / 2, cursorY, { align: 'center' });
        doc.setTextColor(31, 41, 55);
    }
    cursorY += 30;
    
    // --- Section Helper ---
    const drawSection = (title: string, content: () => void) => {
        checkPageBreak(50);
        doc.setFont('helvetica', 'bold').setFontSize(14).text(title.toUpperCase(), margin, cursorY);
        doc.setLineWidth(1.5).line(margin, cursorY + 4, pageW - margin, cursorY + 4);
        cursorY += 25;
        content();
    };

    // --- Summary ---
    if (summary.paragraph || summary.bullets.length > 0) {
        drawSection('Summary', () => {
            if (summary.paragraph) {
                const lines = doc.setFont('helvetica', 'normal').setFontSize(10).splitTextToSize(summary.paragraph, pageW - margin * 2);
                checkPageBreak(lines.length * 12);
                doc.text(lines, margin, cursorY);
                cursorY += lines.length * 12 + 5;
            }
            if (summary.bullets.length > 0) {
                summary.bullets.forEach(bullet => {
                    const bulletLines = doc.splitTextToSize(bullet, pageW - margin * 2 - 15);
                    checkPageBreak(bulletLines.length * 12);
                    doc.text('•', margin + 5, cursorY);
                    doc.text(bulletLines, margin + 15, cursorY);
                    cursorY += bulletLines.length * 12 + 5;
                });
            }
        });
    }

    // --- Work Experience ---
    if (work_experience.length > 0) {
        drawSection('Work Experience', () => {
            work_experience.forEach(job => {
                checkPageBreak(80);
                doc.setFont('helvetica', 'bold').setFontSize(11).text(job.company_name, margin, cursorY);
                const dateText = `${formatDate(job.start_date)} - ${job.is_current ? 'Present' : formatDate(job.end_date)}`;
                doc.setFont('helvetica', 'normal').text(dateText, pageW - margin, cursorY, { align: 'right' });
                cursorY += 14;
                doc.setFont('helvetica', 'bolditalic').setFontSize(10).text(job.job_title, margin, cursorY);
                doc.setFont('helvetica', 'normal').text(job.location, pageW - margin, cursorY, { align: 'right' });
                cursorY += 18;
                job.accomplishments.forEach(acc => {
                    const bulletLines = doc.setFontSize(10).splitTextToSize(acc.description, pageW - margin * 2 - 15);
                    checkPageBreak(bulletLines.length * 12);
                    doc.text('•', margin + 5, cursorY);
                    doc.text(bulletLines, margin + 15, cursorY);
                    cursorY += bulletLines.length * 12 + 4;
                });
                cursorY += 10;
            });
        });
    }

    // --- Education ---
    if (education.length > 0) {
        drawSection('Education', () => {
            education.forEach(edu => {
                checkPageBreak(40);
                doc.setFont('helvetica', 'bold').setFontSize(11).text(edu.school, margin, cursorY);
                const dateText = `${edu.start_year} - ${edu.end_year}`;
                doc.setFont('helvetica', 'normal').text(dateText, pageW - margin, cursorY, { align: 'right' });
                cursorY += 14;
                doc.setFontSize(10).text(`${edu.degree} in ${edu.major.join(', ')}`, margin, cursorY);
                cursorY += 20;
            });
        });
    }

    // --- Skills ---
     if (skills.length > 0) {
        drawSection('Skills', () => {
            skills.forEach(skill => {
                 const skillText = `${skill.heading}: ${skill.items.join(', ')}`;
                 const lines = doc.setFont('helvetica', 'normal').setFontSize(10).splitTextToSize(skillText, pageW - margin * 2);
                 checkPageBreak(lines.length * 12);
                 doc.setFont('helvetica', 'bold').text(`${skill.heading}: `, margin, cursorY, { isInputVisual: false, isOutputVisual: false });
                 const headingWidth = doc.getTextWidth(`${skill.heading}: `);
                 doc.setFont('helvetica', 'normal').text(skill.items.join(', '), margin + headingWidth, cursorY);
                 cursorY += 15;
            });
        });
    }
    
    const filename = `${header.first_name || 'Resume'} ${header.last_name || ''} - ${header.job_title} - ${companyName}.pdf`;
    doc.save(filename);
};

const resumeToPlainText = (resume: Resume): string => {
    let text = `${resume.header.first_name} ${resume.header.last_name}\n`;
    text += `${resume.header.job_title}\n`;
    text += `${resume.header.city}, ${resume.header.state} | ${resume.header.email} | ${resume.header.phone_number}\n`;
    text += (resume.header.links || []).join(' | ') + '\n\n';

    text += 'SUMMARY\n' + '-'.repeat(20) + '\n';
    if(resume.summary.paragraph) text += resume.summary.paragraph + '\n\n';
    if(resume.summary.bullets.length > 0) text += resume.summary.bullets.map(b => `• ${b}`).join('\n') + '\n\n';
    
    text += 'WORK EXPERIENCE\n' + '-'.repeat(20) + '\n';
    resume.work_experience.forEach(exp => {
        text += `${exp.company_name}\t\t${formatDate(exp.start_date)} - ${exp.is_current ? 'Present' : formatDate(exp.end_date)}\n`;
        text += `${exp.job_title}\t\t${exp.location}\n`;
        text += exp.accomplishments.map(acc => `• ${acc.description}`).join('\n') + '\n\n';
    });

    text += 'EDUCATION\n' + '-'.repeat(20) + '\n';
    resume.education.forEach(edu => {
        text += `${edu.school}\t\t${edu.start_year} - ${edu.end_year}\n`;
        text += `${edu.degree} in ${edu.major.join(', ')}\n\n`;
    });
    
    text += 'SKILLS\n' + '-'.repeat(20) + '\n';
    resume.skills.forEach(skill => {
        text += `${skill.heading}: ${skill.items.join(', ')}\n`;
    });

    return text;
};

const ExportOption = ({ title, description, icon: Icon, onClick, isLoading = false, buttonText }: { title: string, description: string, icon: React.ElementType, onClick: () => void, isLoading?: boolean, buttonText: string }) => (
    <div className="flex flex-col items-center justify-between p-4 text-center bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700">
        <div className="flex-grow">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/50">
                <Icon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="mt-2 text-base font-semibold leading-6 text-slate-900 dark:text-white">{title}</h3>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
        </div>
        <button
            onClick={onClick}
            className="mt-4 inline-flex items-center justify-center w-full px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
            disabled={isLoading}
        >
            {isLoading ? <LoadingSpinner/> : buttonText}
        </button>
    </div>
);


export const DownloadResumeStep = ({ finalResume, companyName, onNext, onSaveAndStartAnother, isLoading, onOpenJobDetailsModal, onOpenAiAnalysisModal, onClose }: DownloadResumeStepProps): React.ReactNode => {
    const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
    const [isGeneratingDocx, setIsGeneratingDocx] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    
    const handleDownloadPdf = async () => {
        setIsGeneratingPdf(true);
        try {
            await generatePdf(finalResume, companyName);
        } catch (error) {
            console.error("Failed to generate PDF:", error);
        } finally {
            setIsGeneratingPdf(false);
        }
    };
    
    const handleDownloadDocx = async () => {
        setIsGeneratingDocx(true);
        try {
            await generateDocx(finalResume, companyName);
        } catch (error) {
            console.error("Failed to generate DOCX:", error);
        } finally {
            setIsGeneratingDocx(false);
        }
    };
    
    const handleCopyToClipboard = async () => {
        setCopySuccess(false);
        const plainText = resumeToPlainText(finalResume);
        try {
            await navigator.clipboard.writeText(plainText);
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Export Your Resume</h2>
                <p className="mt-1 text-slate-600 dark:text-slate-400">Download your resume, or copy the text to paste into Google Docs or another editor.</p>
            </div>

            {(onOpenJobDetailsModal && onOpenAiAnalysisModal) && (
                 <div className="flex space-x-2">
                    <button
                        type="button"
                        onClick={onOpenJobDetailsModal}
                        className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"
                    >
                        <DocumentTextIcon className="h-5 w-5" />
                        View Job Details
                    </button>
                    <button
                        type="button"
                        onClick={onOpenAiAnalysisModal}
                        className="inline-flex items-center gap-x-1.5 rounded-md bg-white dark:bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600"
                    >
                        <LightBulbIcon className="h-5 w-5" />
                        View AI Analysis
                    </button>
                </div>
            )}
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                 <ExportOption 
                    title="Professional PDF"
                    description="A clean, polished PDF ready to send. Best for direct applications."
                    icon={DocumentTextIcon}
                    onClick={handleDownloadPdf}
                    isLoading={isGeneratingPdf}
                    buttonText="Download PDF"
                />
                <ExportOption 
                    title="Editable DOCX"
                    description="A .docx file optimized for Google Docs. Best for making final manual edits."
                    icon={ClipboardDocumentListIcon}
                    onClick={handleDownloadDocx}
                    isLoading={isGeneratingDocx}
                    buttonText="Download .docx"
                />
                 <ExportOption 
                    title="Copy to Clipboard"
                    description="Copies formatted text. Best for quickly pasting into a new Google Doc or email."
                    icon={ClipboardDocumentCheckIcon}
                    onClick={handleCopyToClipboard}
                    isLoading={copySuccess}
                    buttonText={copySuccess ? 'Copied!' : 'Copy Text'}
                />
            </div>

            <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
                {onClose ? (
                    <button
                        onClick={onClose}
                        disabled={isLoading || isGeneratingPdf || isGeneratingDocx}
                        className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                    >
                        Close
                    </button>
                ) : (
                    <div className="flex items-center justify-between w-full">
                        {onSaveAndStartAnother && (
                            <button
                                onClick={onSaveAndStartAnother}
                                disabled={isLoading || isGeneratingPdf || isGeneratingDocx}
                                className="px-6 py-2 text-base font-medium rounded-lg text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 border border-slate-300 dark:border-slate-500 shadow-sm transition-colors disabled:opacity-50"
                            >
                                Save & Start Another
                            </button>
                        )}
                        {onNext && (
                             <button
                                onClick={onNext}
                                disabled={isLoading || isGeneratingPdf || isGeneratingDocx}
                                className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors disabled:bg-green-400"
                            >
                                {isLoading ? <LoadingSpinner /> : 'Next: Answer Questions'}
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
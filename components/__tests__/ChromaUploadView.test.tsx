import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { vi } from 'vitest';
import { ChromaUploadView } from '../ChromaUploadView';
import { ToastProvider } from '../../hooks/useToast';
import * as apiService from '../../services/apiService';
import { StrategicNarrative, UploadedDocument } from '../../types';

vi.mock('../../services/apiService', () => ({
    getUploadedDocuments: vi.fn(),
    uploadCareerBrand: vi.fn(),
    uploadCareerPath: vi.fn(),
    uploadJobSearchStrategy: vi.fn(),
    deleteUploadedDocument: vi.fn(),
    createProofPoint: vi.fn(),
    createResumeDocument: vi.fn(),
    updateResumeDocument: vi.fn(),
    getDocumentDetail: vi.fn(),
}));

type MockedApi = {
    getUploadedDocuments: ReturnType<typeof vi.fn>;
    createProofPoint: ReturnType<typeof vi.fn>;
    createResumeDocument: ReturnType<typeof vi.fn>;
    updateResumeDocument: ReturnType<typeof vi.fn>;
    getDocumentDetail: ReturnType<typeof vi.fn>;
};

const mockedApi = apiService as unknown as MockedApi;

describe('ChromaUploadView', () => {
    const mockNarratives: StrategicNarrative[] = [
        {
            narrative_id: 'narrative-1',
            narrative_name: 'North Star Narrative',
            company_id: null,
            created_at: '',
            updated_at: '',
            user_id: 'user-1',
            impact_stories: [],
            common_interview_answers: [],
        },
    ];

    const proofPointDoc: UploadedDocument = {
        id: 'proof-1',
        profile_id: 'narrative-1',
        title: 'Led AI Adoption',
        section: 'General',
        content_type: 'proof_points',
        collection_name: 'proof_points',
        created_at: '2024-01-01T00:00:00.000Z',
        metadata: {
            status: 'draft',
            is_latest: true,
            role_title: 'Product Lead',
            company: 'Acme',
        },
    };

    const resumeDoc: UploadedDocument = {
        id: 'resume-1',
        profile_id: 'narrative-1',
        title: 'Resume Draft',
        section: 'resume',
        content_type: 'resumes',
        collection_name: 'resumes',
        created_at: '2024-01-02T00:00:00.000Z',
        metadata: {
            status: 'draft',
            is_latest: true,
            selected_proof_points: [],
        },
    };

    const baseDocs: UploadedDocument[] = [proofPointDoc, resumeDoc];

    const renderComponent = () =>
        render(
            <ToastProvider>
                <ChromaUploadView strategicNarratives={mockNarratives} activeNarrativeId="narrative-1" />
            </ToastProvider>,
        );

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('submits proof point metadata and refreshes document listings', async () => {
        const newProofDoc: UploadedDocument = {
            ...proofPointDoc,
            id: 'proof-2',
            title: 'Platform Launch',
            metadata: {
                ...proofPointDoc.metadata,
                status: 'draft',
                is_latest: true,
            },
        };

        (mockedApi.getUploadedDocuments as any)
            .mockResolvedValueOnce(baseDocs)
            .mockResolvedValueOnce([...baseDocs, newProofDoc])
            .mockResolvedValue([...baseDocs, newProofDoc]);

        (mockedApi.createProofPoint as any).mockResolvedValue({ status: 'success', data: { document_id: 'proof-2' } });

        renderComponent();
        await waitFor(() => expect(mockedApi.getUploadedDocuments).toHaveBeenCalledTimes(1));

        fireEvent.click(screen.getByRole('button', { name: /proof points/i }));
        fireEvent.change(screen.getByLabelText(/Role Title/i), { target: { value: 'Product Lead' } });
        fireEvent.change(screen.getByLabelText(/Company/i), { target: { value: 'Acme' } });
        fireEvent.change(screen.getByLabelText(/^Location$/i), { target: { value: 'Remote' } });
        fireEvent.change(screen.getByLabelText(/^Start Date$/i), { target: { value: '2023-01-01' } });
        fireEvent.click(screen.getByLabelText(/Current Role/i));
        fireEvent.change(screen.getByLabelText('Skills (comma separated)'), { target: { value: 'growth, ai' } });
        fireEvent.change(screen.getByLabelText('Keywords (comma separated)'), {
            target: { value: 'strategy, analytics' },
        });
        fireEvent.change(screen.getByLabelText('Architecture (comma separated)'), {
            target: { value: 'GCP, Kubernetes' },
        });
        fireEvent.change(screen.getByLabelText(/^Content$/i), {
            target: { value: 'Scaled the AI platform with cross-functional pods.' },
        });

        fireEvent.click(screen.getByRole('button', { name: /save proof point/i }));

        await waitFor(() =>
            expect(mockedApi.createProofPoint).toHaveBeenCalledWith(
                expect.objectContaining({
                    profile_id: 'narrative-1',
                    title: 'Acme - Product Lead',
                    impact_tags: ['growth', 'ai'],
                    job_metadata: {
                        keywords: ['strategy', 'analytics'],
                        architecture: ['GCP', 'Kubernetes'],
                    },
                }),
            ),
        );

        await waitFor(() => expect(mockedApi.getUploadedDocuments).toHaveBeenCalledTimes(2));
        await screen.findByText(/Platform Launch/i);
        const latestBadges = await screen.findAllByText(/Latest/i);
        expect(latestBadges.length).toBeGreaterThan(0);
    });

    it('submits resume draft metadata including proof points', async () => {
        const updatedResume: UploadedDocument = {
            ...resumeDoc,
            metadata: {
                status: 'approved',
                is_latest: true,
                selected_proof_points: ['proof-1'],
                approved_by: 'reviewer@example.com',
            },
        };

        (mockedApi.getUploadedDocuments as any)
            .mockResolvedValueOnce(baseDocs)
            .mockResolvedValueOnce([proofPointDoc, updatedResume])
            .mockResolvedValue([proofPointDoc, updatedResume]);

        (mockedApi.createResumeDocument as any).mockResolvedValue({ status: 'success', data: { document_id: 'resume-2' } });

        renderComponent();
        await waitFor(() => expect(mockedApi.getUploadedDocuments).toHaveBeenCalledTimes(1));

        fireEvent.click(screen.getByRole('button', { name: /resumes/i }));
        fireEvent.change(screen.getByLabelText(/^Title$/i), { target: { value: 'Principal PM Resume' } });
        fireEvent.change(screen.getByLabelText(/Role \/ Company Target/i), { target: { value: 'Principal PM @ Acme' } });
        fireEvent.change(screen.getAllByLabelText(/^Status$/i)[0], { target: { value: 'approved' } });
        const resumeSection = screen.getByRole('heading', { name: /Upload Resume Draft/i }).closest('div') as HTMLElement;
        fireEvent.click(within(resumeSection).getByLabelText(/Led AI Adoption/i));
        fireEvent.change(screen.getByLabelText(/Skills Highlighted/i), { target: { value: 'ai strategy' } });
        fireEvent.change(screen.getAllByLabelText(/^Reviewer Email$/i)[0], {
            target: { value: 'reviewer@example.com' },
        });
        fireEvent.change(screen.getAllByLabelText(/^Reviewer Notes$/i)[0], { target: { value: 'Looks strong' } });
        fireEvent.change(screen.getByLabelText(/^Resume Content$/i), {
            target: { value: 'Extensive experience shipping AI products.' },
        });

        fireEvent.click(screen.getByRole('button', { name: /upload resume draft/i }));

        await waitFor(() =>
            expect(mockedApi.createResumeDocument).toHaveBeenCalledWith(
                expect.objectContaining({
                    profile_id: 'narrative-1',
                    title: 'Principal PM Resume',
                    status: 'approved',
                    selected_proof_points: ['proof-1'],
                    additional_metadata: { skills: ['ai strategy'] },
                    approved_by: 'reviewer@example.com',
                }),
            ),
        );

        await waitFor(() => expect(mockedApi.getUploadedDocuments).toHaveBeenCalledTimes(2));
        await screen.findByText(/Status: approved/i);
        const updatedLatestBadges = await screen.findAllByText(/Latest/i);
        expect(updatedLatestBadges.length).toBeGreaterThan(0);
    });

    it('patches resume metadata during approval flow', async () => {
        const draftResume: UploadedDocument = {
            ...resumeDoc,
            metadata: {
                status: 'in_review',
                is_latest: false,
                selected_proof_points: ['proof-1'],
            },
        };

        const secondProof: UploadedDocument = {
            ...proofPointDoc,
            id: 'proof-2',
            title: 'Operational Excellence',
        };

        const approvedResume: UploadedDocument = {
            ...resumeDoc,
            metadata: {
                status: 'approved',
                is_latest: true,
                selected_proof_points: ['proof-1', 'proof-2'],
                approved_by: 'approver@example.com',
            },
        };

        (mockedApi.getUploadedDocuments as any)
            .mockResolvedValueOnce([secondProof, draftResume])
            .mockResolvedValueOnce([secondProof, approvedResume])
            .mockResolvedValue([secondProof, approvedResume]);

        (mockedApi.updateResumeDocument as any).mockResolvedValue({ status: 'success', data: { document_id: 'resume-1' } });

        renderComponent();
        await waitFor(() => expect(mockedApi.getUploadedDocuments).toHaveBeenCalledTimes(1));

        fireEvent.click(screen.getByRole('button', { name: /resumes/i }));
        fireEvent.change(screen.getByLabelText(/Select Resume/i), { target: { value: 'resume-1' } });

        const approvalSection = screen.getByRole('heading', { name: /Approval & Status Updates/i }).closest('div') as HTMLElement;
        const approvalLatestCheckbox = within(approvalSection).getByLabelText(/Mark as latest version/i) as HTMLInputElement;
        await waitFor(() => expect(approvalLatestCheckbox).not.toBeChecked());

        fireEvent.change(within(approvalSection).getByLabelText(/^Status$/i), { target: { value: 'approved' } });
        fireEvent.click(approvalLatestCheckbox);
        fireEvent.click(within(approvalSection).getByLabelText(/Operational Excellence/i));
        fireEvent.change(within(approvalSection).getByLabelText(/^Reviewer Email$/i), {
            target: { value: 'approver@example.com' },
        });
        fireEvent.change(within(approvalSection).getByLabelText(/^Reviewer Notes$/i), { target: { value: 'Ship it' } });

        fireEvent.click(screen.getByRole('button', { name: /Submit Approval Update/i }));

        await waitFor(() =>
            expect(mockedApi.updateResumeDocument).toHaveBeenCalledWith(
                'resume-1',
                expect.objectContaining({
                    status: 'approved',
                    is_latest: true,
                    approved_by: 'approver@example.com',
                    approval_notes: 'Ship it',
                    selected_proof_points: ['proof-1', 'proof-2'],
                }),
            ),
        );

        await waitFor(() => expect(mockedApi.getUploadedDocuments).toHaveBeenCalledTimes(2));
        await screen.findByText(/Status: approved/i);
        const approvalLatestBadges = await screen.findAllByText(/Latest/i);
        expect(approvalLatestBadges.length).toBeGreaterThan(0);
    });
});

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getReviewedJobs, ReviewedJobsFilters, ReviewedJobsSort } from '../services/apiService';
import { ReviewedJob, PaginatedResponse, ReviewedJobRecommendation } from '../types';
import { LoadingSpinner, CheckIcon, XCircleIcon, TableCellsIcon, Squares2X2Icon, PlusCircleIcon, UsersIcon } from './IconComponents';
import { JobReviewModal } from './JobReviewModal';
import { JobCardView } from './JobCardView';
import { useToast } from '../hooks/useToast';

const SortableHeader = ({ label, sortKey, currentSort, onSort }: { label: string, sortKey: ReviewedJobsSort['by'], currentSort: ReviewedJobsSort, onSort: (by: ReviewedJobsSort['by']) => void }) => {
    const isCurrent = currentSort.by === sortKey;
    const arrow = isCurrent ? (currentSort.order === 'desc' ? '▼' : '▲') : '';
    return (
        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white cursor-pointer" onClick={() => onSort(sortKey)}>
            {label} {arrow}
        </th>
    );
};

const RecommendationBadge = ({ recommendation, hasOverride }: { recommendation: ReviewedJobRecommendation, hasOverride?: boolean }) => {
    const classes: Record<ReviewedJobRecommendation, string> = {
        'Recommended': 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
        'Not Recommended': 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
    };
    return (
        <div className="flex items-center gap-2">
            <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${classes[recommendation]}`}>
                {recommendation}
            </span>
            {hasOverride && (
                <span className="inline-flex items-center rounded-md bg-blue-100 dark:bg-blue-900/50 px-2 py-1 text-xs font-medium text-blue-800 dark:text-blue-300">
                    HITL Override
                </span>
            )}
        </div>
    );
};

export const ReviewedJobsView = () => {
    const navigate = useNavigate();
    const [data, setData] = useState<PaginatedResponse<ReviewedJob> | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [filters, setFilters] = useState<ReviewedJobsFilters>({ recommendation: 'Recommended' });
    const [sort, setSort] = useState<ReviewedJobsSort>({ by: 'overall_alignment_score', order: 'desc' });
    const [minScoreFilter, setMinScoreFilter] = useState('');
    const [selectedJob, setSelectedJob] = useState<ReviewedJob | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [viewMode, setViewMode] = useState<'table' | 'cards'>('cards');
    const { addToast } = useToast();

    const handleJobRemoval = useCallback((jobId: string) => {
        setData(prev => {
            if (!prev) {
                return prev;
            }

            const filteredItems = prev.items.filter(item => item.job_id !== jobId);
            return {
                ...prev,
                items: filteredItems
            };
        });
    }, []);

    const fetchJobs = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const currentFilters = {
                ...filters,
                min_score: minScoreFilter ? Number(minScoreFilter) : undefined,
            };
            const result = await getReviewedJobs({ page, size: 15, filters: currentFilters, sort });
            setData(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch reviewed jobs.');
        } finally {
            setIsLoading(false);
        }
    }, [page, filters, sort, minScoreFilter]);

    useEffect(() => {
        const handler = setTimeout(() => {
            fetchJobs();
        }, 300); // Debounce all changes slightly

        return () => clearTimeout(handler);
    }, [fetchJobs]);

    const handleSortChange = (by: ReviewedJobsSort['by']) => {
        setPage(1); // Reset page on change
        setSort(prev => ({
            by,
            order: prev.by === by && prev.order === 'desc' ? 'asc' : 'desc'
        }));
    };

    const handleRecommendationFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setPage(1); // Reset page on change
        setFilters(prev => ({ ...prev, recommendation: e.target.value as ReviewedJobsFilters['recommendation'] }));
    };

    const handleScoreFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        if (value === '' || (/^\d*\.?\d*$/.test(value) && Number(value) >= 0 && Number(value) <= 10)) {
            setPage(1); // Reset page on change
            setMinScoreFilter(value);
        }
    };

    const handleReviewClick = (job: ReviewedJob) => {
        setSelectedJob(job);
        setIsModalOpen(true);
    };

    const handleModalClose = () => {
        setIsModalOpen(false);
        setSelectedJob(null);
    };

    const handleOverrideSuccess = (jobId: string, message: string) => {
        handleJobRemoval(jobId);
        addToast(message, 'success');
    };

    const renderTable = () => {
        if (!data || data.items.length === 0) {
            return (
                <div className="text-center py-20 bg-white dark:bg-slate-800 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
                    <UsersIcon className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-slate-900 dark:text-slate-300">There are no Job Postings to Review at this time.</h3>
                    <p className="mt-1 text-slate-500 dark:text-slate-400">Please check back later or adjust your filters.</p>
                </div>
            );
        }

        return (
            <div className="-mx-4 sm:-mx-6 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead className="bg-slate-50 dark:bg-slate-800">
                        <tr>
                            <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-white sm:pl-6">Job Title</th>
                            <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Company</th>
                            <SortableHeader label="Date Posted" sortKey="date_posted" currentSort={sort} onSort={handleSortChange} />
                            <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Recommendation</th>
                            <SortableHeader label="Alignment Score" sortKey="overall_alignment_score" currentSort={sort} onSort={handleSortChange} />
                            <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Eligible to Apply</th>
                            <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900 dark:text-white">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-slate-700 bg-white dark:bg-slate-800">
                        {data.items.map(job => {
                            const hasOverride = job.override_recommend !== null && job.override_recommend !== undefined;
                            const finalRecommendation = hasOverride
                                ? (job.override_recommend ? 'Recommended' : 'Not Recommended')
                                : job.recommendation;
                            const finalEligibility = hasOverride
                                ? job.override_recommend
                                : job.is_eligible_for_application;

                            return (
                                <tr key={job.job_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                                    <td className="py-4 pl-4 pr-3 text-sm sm:pl-6">
                                        <a href={job.url ?? '#'} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 dark:text-blue-400 hover:underline">{job.title ?? 'Untitled Role'}</a>
                                        <div className="text-gray-500 dark:text-slate-400">{job.location ?? '—'}</div>
                                    </td>
                                    <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400">{job.company_name ?? '—'}</td>
                                    <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400">{job.date_posted ? new Date(job.date_posted).toLocaleDateString() : '—'}</td>
                                    <td className="px-3 py-4 text-sm">
                                        <RecommendationBadge
                                            recommendation={finalRecommendation as ReviewedJobRecommendation}
                                            hasOverride={hasOverride}
                                        />
                                    </td>
                                    <td className="px-3 py-4 text-sm font-semibold text-gray-900 dark:text-white">{job.overall_alignment_score.toFixed(1)}</td>
                                    <td className="px-3 py-4 text-sm text-center">
                                        {finalEligibility ? <CheckIcon className="h-6 w-6 text-green-500 mx-auto" /> : <XCircleIcon className="h-6 w-6 text-slate-400 mx-auto" />}
                                    </td>
                                    <td className="px-3 py-4 text-sm text-center">
                                        <button
                                            onClick={() => handleReviewClick(job)}
                                            className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-800/50 transition-colors"
                                        >
                                            Review
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        );
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">AI Job Board</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Jobs automatically reviewed by the AI based on your active narrative.</p>
                </div>
                <button
                    onClick={() => navigate('/add-manual-job')}
                    className="inline-flex items-center justify-center w-full md:w-auto px-5 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                    <PlusCircleIcon className="w-5 h-5 mr-2 -ml-1" />
                    Add Manual Job
                </button>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-4 sm:p-6 border border-slate-200 dark:border-slate-700">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-4 w-full sm:w-auto">
                        <div>
                            <label htmlFor="recommendation-filter" className="block text-xs font-medium text-slate-500">Recommendation</label>
                            <select id="recommendation-filter" value={filters.recommendation} onChange={handleRecommendationFilter} className="mt-1 block w-full sm:w-auto rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm">
                                <option value="All">All</option>
                                <option value="Recommended">Recommended</option>
                                <option value="Not Recommended">Not Recommended</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="score-filter" className="block text-xs font-medium text-slate-500">Min. Score</label>
                            <input type="number" id="score-filter" value={minScoreFilter} onChange={handleScoreFilterChange} min="0" max="10" step="0.1" className="mt-1 block w-full sm:w-24 rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm" placeholder="e.g., 7.5" />
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setViewMode('cards')}
                            className={`p-2 rounded-lg ${viewMode === 'cards' ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}`}
                            title="Card view"
                        >
                            <Squares2X2Icon className="h-5 w-5" />
                        </button>
                        <button
                            onClick={() => setViewMode('table')}
                            className={`p-2 rounded-lg ${viewMode === 'table' ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}`}
                            title="Table view"
                        >
                            <TableCellsIcon className="h-5 w-5" />
                        </button>
                    </div>
                </div>
                <div className="mt-4">
                    {isLoading ? (
                        <div className="flex justify-center items-center p-8"><LoadingSpinner /><span className="ml-2">Loading...</span></div>
                    ) : error ? (
                        <div className="p-4 bg-red-50 text-red-700 rounded-md">Error: {error}</div>
                    ) : viewMode === 'cards' ? (
                        (data && data.items.length > 0) ? (
                            <JobCardView
                                jobs={data.items}
                                onOverrideSuccess={handleOverrideSuccess}
                                currentPage={page}
                                onPageChange={setPage}
                                isLoading={isLoading}
                                activeNarrativeId={undefined} // TODO: Pass actual active narrative from parent
                            />
                        ) : (
                            <div className="text-center py-20 bg-white dark:bg-slate-800 rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
                                <UsersIcon className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-slate-900 dark:text-slate-300">There are no Job Postings to Review at this time.</h3>
                                <p className="mt-1 text-slate-500 dark:text-slate-400">Please check back later or adjust your filters.</p>
                            </div>
                        )
                    ) : renderTable()}
                </div>
                {!isLoading && data && data.pages > 1 && (
                    <div className="flex items-center justify-between mt-4">
                        <button onClick={() => setPage(p => p - 1)} disabled={page <= 1} className="px-4 py-2 text-sm font-medium rounded-md border border-slate-300 dark:border-slate-600 disabled:opacity-50">Previous</button>
                        <span className="text-sm text-slate-500">Page {data.page} of {data.pages}</span>
                        <button onClick={() => setPage(p => p + 1)} disabled={page >= data.pages} className="px-4 py-2 text-sm font-medium rounded-md border border-slate-300 dark:border-slate-600 disabled:opacity-50">Next</button>
                    </div>
                )}
            </div>

            {/* Job Review Modal */}
            <JobReviewModal
                job={selectedJob}
                isOpen={isModalOpen}
                onClose={handleModalClose}
                onOverrideSuccess={handleOverrideSuccess}
            />
        </div>
    );
};

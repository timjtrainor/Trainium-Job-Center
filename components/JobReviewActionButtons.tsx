"use client";

import React from 'react';
import { ArrowRightIcon } from './IconComponents';

interface JobReview {
  overallAlignmentScore?: number;
  recommend?: boolean;
  crewOutput?: {
    constraints?: {
      readable_constraint_issues?: string;
    };
  };
}

interface JobReviewActionButtonsProps {
  jobReview: JobReview;
  jobId: string;
  onProceedApplication: (jobId: string) => void;
  onResearchMore: (jobId: string) => void;
  onArchiveJob: (jobId: string, reason: string) => void;
  onApplyOverride: (jobId: string, overrideData: any) => void;
  isProcessing?: boolean;
}

export function JobReviewActionButtons({
  jobReview,
  jobId,
  onProceedApplication,
  onResearchMore,
  onArchiveJob,
  onApplyOverride,
  isProcessing = false
}: JobReviewActionButtonsProps) {
  const hasDealBreakers = jobReview.crewOutput?.constraints?.readable_constraint_issues &&
    jobReview.crewOutput.constraints.readable_constraint_issues !== 'No constraint violations detected';

  const isRecommended = jobReview.recommend && !hasDealBreakers;
  const shouldDisableProceed = !isRecommended || hasDealBreakers;

  // Smart defaults based on scoring
  const getDefaultAction = () => {
    if (hasDealBreakers) return 'archive';
    if (isRecommended) return 'proceed';
    const score = jobReview.overallAlignmentScore;
    if (score && score >= 7.6) return 'research'; // Borderline but could be worth pursuing
    return 'archive';
  };

  const handleProceed = () => {
    onProceedApplication(jobId);
  };

  const handleResearch = () => {
    onResearchMore(jobId);
  };

  const handleArchive = () => {
    const reason = hasDealBreakers ? 'deal_breakers' : 'low_alignment';
    onArchiveJob(jobId, reason);
  };

  const handleOverride = () => {
    // Optional: Could show a modal for manual override
    onApplyOverride(jobId, {
      reason: 'manual_override',
      originalRecommendation: jobReview.recommend,
      timestamp: new Date().toISOString()
    });
  };

  const defaultAction = getDefaultAction();

  return (
    <div className="space-y-4">
      {/* Primary Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Proceed with Application - Primary Action */}
        <button
          onClick={handleProceed}
          disabled={shouldDisableProceed || isProcessing}
          className={`
            flex-1 px-4 py-3 text-sm font-semibold rounded-lg transition-all duration-200
            ${shouldDisableProceed
              ? 'bg-slate-100 text-slate-400 cursor-not-allowed dark:bg-slate-800 dark:text-slate-600'
              : 'bg-green-600 hover:bg-green-700 text-white shadow-sm hover:shadow-md focus:ring-2 focus:ring-green-500 focus:ring-offset-2'
            }
          `}
        >
          <div className="flex items-center justify-center gap-2">
            <span>🚀 Proceed with Application</span>
            <ArrowRightIcon className="h-4 w-4" />
          </div>
          {shouldDisableProceed && (
            <div className="text-xs mt-1 opacity-75">
              {hasDealBreakers ? 'Resolve critical issues first' : 'Not recommended'}
            </div>
          )}
        </button>

        {/* Research More - Secondary Action */}
        <button
          onClick={handleResearch}
          disabled={isProcessing}
          className="flex-1 px-4 py-3 text-sm font-medium rounded-lg border-2 border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/40 transition-colors duration-200 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          <div className="flex items-center justify-center gap-2">
            <span>🔍 Research More Details</span>
          </div>
          <div className="text-xs mt-1 opacity-75">
            Gather additional information
          </div>
        </button>

        {/* Archive - Danger Action */}
        <button
          onClick={handleArchive}
          disabled={isProcessing}
          className="flex-1 px-4 py-3 text-sm font-medium rounded-lg bg-red-600 hover:bg-red-700 text-white shadow-sm hover:shadow-md focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200"
        >
          <div className="flex items-center justify-center gap-2">
            <span>❌ Pass on This Opportunity</span>
          </div>
          <div className="text-xs mt-1 opacity-90">
            {hasDealBreakers ? 'Critical issues present' : 'Low alignment match'}
          </div>
        </button>
      </div>

      {/* Smart Defaults Hint */}
      <div className="text-center">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          <span className="font-medium">Smart Default:</span> Based on the analysis,
          this job will {defaultAction === 'proceed' ? 'advance to application stage' :
                           defaultAction === 'research' ? 'suggest research phase' :
                           'archive automatically'}
        </p>
      </div>

      {/* Manual Override Option */}
      {!isRecommended && !hasDealBreakers && (
        <div className="flex justify-center">
          <button
            onClick={handleOverride}
            disabled={isProcessing}
            className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 underline underline-offset-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-sm px-2 py-1"
          >
            Apply Manual Override
          </button>
        </div>
      )}

      {/* Processing Indicator */}
      {isProcessing && (
        <div className="flex items-center justify-center gap-2 text-slate-500 dark:text-slate-400">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-500"></div>
          <span className="text-sm">Processing your decision...</span>
        </div>
      )}
    </div>
  );
}

export default JobReviewActionButtons;

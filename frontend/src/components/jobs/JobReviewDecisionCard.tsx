"use client";

import React from 'react';
import { CheckBadgeIcon, XCircleIcon, ClockIcon } from '../shared/ui/IconComponents';

interface JobReview {
  overallAlignmentScore?: number;
  recommend?: boolean;
  confidence?: 'high' | 'medium' | 'low';
  rationale?: string;
  crewOutput?: {
    constraints?: {
      constraint_issues?: string;
    };
    readable_constraint_issues?: string;
    [key: string]: any;
  };
}

interface JobReviewDecisionCardProps {
  jobReview: JobReview;
}

export function JobReviewDecisionCard({ jobReview }: JobReviewDecisionCardProps) {
  const getScoreBadge = (score?: number) => {
    if (!score && score !== 0) return { text: 'Pending Analysis', class: 'bg-slate-100 text-slate-600' };

    if (score >= 8.5) return { text: '⭐ Exceptional Match', class: 'bg-green-100 text-green-800' };
    if (score >= 8.25) return { text: '✅ Strong Recommendation', class: 'bg-green-100 text-green-800' };
    if (score >= 7.9) return { text: '👍 Good Opportunity', class: 'bg-blue-100 text-blue-800' };
    if (score >= 7.6) return { text: '🤔 Borderline - Consider Carefully', class: 'bg-yellow-100 text-yellow-800' };
    if (score >= 7.0) return { text: '⚠️ Potential Concerns - Research More', class: 'bg-orange-100 text-orange-800' };
    return { text: '❌ Not Recommended', class: 'bg-red-100 text-red-800' };
  };

  const getConfidenceIcon = (confidence?: string) => {
    switch (confidence) {
      case 'high': return <CheckBadgeIcon className="h-4 w-4 text-green-600" />;
      case 'medium': return <CheckBadgeIcon className="h-4 w-4 text-blue-600" />;
      case 'low': return <XCircleIcon className="h-4 w-4 text-red-600" />;
      default: return <ClockIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const hasDealBreakers = jobReview.crewOutput?.readable_constraint_issues &&
    jobReview.crewOutput.readable_constraint_issues !== 'No constraint violations detected';

  const scoreBadge = getScoreBadge(jobReview.overallAlignmentScore);

  return (
    <div className={`w-full bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm p-6 ${hasDealBreakers ? 'border-l-red-500' : 'border-l-green-500'}`}>
      <div className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getConfidenceIcon(jobReview.confidence)}
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              AI Job Analysis Results
            </h3>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-slate-900 dark:text-white">
              {jobReview.overallAlignmentScore?.toFixed(1) || '--'}/10
            </div>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${scoreBadge.class}`}>
              {scoreBadge.text}
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {/* Deal Breaker Alerts - Priority 1 */}
        {hasDealBreakers && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <XCircleIcon className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-semibold text-red-800 dark:text-red-200">🚨 Critical Issues Detected</h4>
                <p className="text-red-700 dark:text-red-300 text-sm mt-1">
                  {jobReview.crewOutput?.readable_constraint_issues}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Recommendation Banner */}
        <div className={`rounded-lg p-4 ${
          jobReview.recommend && !hasDealBreakers
            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
            : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
        }`}>
          <div className="flex items-center gap-2">
            {jobReview.recommend && !hasDealBreakers ? (
              <CheckBadgeIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
            ) : (
              <XCircleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            )}
            <div className="flex-1">
              <p className="font-semibold text-slate-900 dark:text-slate-100">
                {jobReview.recommend && !hasDealBreakers
                  ? `✅ Strong Recommendation - ${jobReview.confidence} confidence`
                  : `⚠️ High-Value Rejection - ${jobReview.confidence} confidence`
                }
              </p>
              <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">{jobReview.rationale}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default JobReviewDecisionCard;

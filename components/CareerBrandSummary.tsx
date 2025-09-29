"use client";

import React, { useState } from 'react';
import { ChevronUpDownIcon, CheckBadgeIcon, ClockIcon, XCircleIcon } from './IconComponents';

interface CareerBrandSummaryProps {
  crewOutput: {
    constraints?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    compensation_philosophy?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    trajectory_mastery?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    north_star?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    values_compass?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    lifestyle_alignment?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    purpose_impact?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    industry_focus?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    company_filters?: {
      overall_alignment_score?: number;
      score?: number;
      readable_explanation?: string;
    };
    [key: string]: any;
  };
}

interface SummaryCardProps {
  title: string;
  icon: React.ReactNode;
  priority: 'high' | 'medium' | 'low';
  dimensions: Array<{
    name: string;
    score?: number;
    explanation?: string;
    isPositive?: boolean;
  }>;
  defaultExpanded?: boolean;
}

function SummaryCard({ title, icon, priority, dimensions, defaultExpanded = false }: SummaryCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const getPriorityStyles = () => {
    switch (priority) {
      case 'high':
        return {
          header: 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 dark:from-green-900/20 dark:to-emerald-900/20 dark:border-green-800',
          icon: 'text-green-600 dark:text-green-400',
          title: 'text-green-800 dark:text-green-200'
        };
      case 'medium':
        return {
          header: 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200 dark:from-blue-900/20 dark:to-cyan-900/20 dark:border-blue-800',
          icon: 'text-blue-600 dark:text-blue-400',
          title: 'text-blue-800 dark:text-blue-200'
        };
      case 'low':
        return {
          header: 'bg-gradient-to-r from-slate-50 to-zinc-50 border-slate-200 dark:from-slate-900/20 dark:to-zinc-900/20 dark:border-slate-800',
          icon: 'text-slate-600 dark:text-slate-400',
          title: 'text-slate-800 dark:text-slate-200'
        };
    }
  };

  const styles = getPriorityStyles();
  const hasContent = dimensions.length > 0;

  if (!hasContent && priority !== 'high') return null; // Hide empty non-priority sections

  return (
    <div className={`border rounded-lg overflow-hidden ${styles.header}`} onClick={() => setIsExpanded(!isExpanded)}>
      <div className="px-4 py-3 cursor-pointer hover:opacity-90 transition-opacity">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={styles.icon}>{icon}</span>
            <h4 className={`font-semibold ${styles.title}`}>{title}</h4>
            <span className="text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 px-2 py-0.5 rounded-full">
              {dimensions.length} items
            </span>
          </div>
          <ChevronUpDownIcon className={`h-4 w-4 text-slate-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {isExpanded && hasContent && (
        <div className="bg-white dark:bg-slate-800 border-t border-inherit">
          {dimensions.map((dimension, idx) => (
            <div key={idx} className={`px-4 py-3 border-b border-slate-100 dark:border-slate-700 last:border-b-0`}>
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex-shrink-0">
                  {dimension.score !== undefined ? (
                    dimension.score >= 4 ? (
                      <CheckBadgeIcon className="h-4 w-4 text-green-600" />
                    ) : dimension.score >= 2.5 ? (
                      <ClockIcon className="h-4 w-4 text-blue-600" />
                    ) : (
                      <XCircleIcon className="h-4 w-4 text-red-600" />
                    )
                  ) : (
                    <ClockIcon className="h-4 w-4 text-gray-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-1">
                    {dimension.name}
                    {dimension.score !== undefined && (
                      <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">
                        ({dimension.score}/5)
                      </span>
                    )}
                  </p>
                  {dimension.explanation && (
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {dimension.explanation}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function CareerBrandSummary({ crewOutput }: CareerBrandSummaryProps) {
  // Extract positive/high-scoring dimensions
  const getPositiveDimensions = () => {
    const dimensions = [
      { key: 'constraints', name: 'Hard Requirements', data: crewOutput.constraints },
      { key: 'compensation_philosophy', name: 'Compensation Philosophy', data: crewOutput.compensation_philosophy },
      { key: 'trajectory_mastery', name: 'Trajectory & Growth', data: crewOutput.trajectory_mastery },
      { key: 'north_star', name: 'North Star Alignment', data: crewOutput.north_star },
      { key: 'values_compass', name: 'Values Alignment', data: crewOutput.values_compass },
      { key: 'lifestyle_alignment', name: 'Lifestyle Fit', data: crewOutput.lifestyle_alignment },
      { key: 'purpose_impact', name: 'Purpose & Impact', data: crewOutput.purpose_impact },
      { key: 'industry_focus', name: 'Industry Focus', data: crewOutput.industry_focus },
      { key: 'company_filters', name: 'Company Culture', data: crewOutput.company_filters },
    ];

    return dimensions
      .filter(dim => dim.data?.score && dim.data.score >= 4)
      .map(dim => ({
        name: dim.name,
        score: dim.data.score,
        explanation: dim.data.readable_explanation,
        isPositive: true
      }))
      .sort((a, b) => (b.score || 0) - (a.score || 0)) // Sort by score desc
      .slice(0, 3); // Top 3
  };

  // Extract concerning dimensions
  const getConcerningDimensions = () => {
    const dimensions = [
      { key: 'constraints', name: 'Hard Requirements', data: crewOutput.constraints },
      { key: 'compensation_philosophy', name: 'Compensation Philosophy', data: crewOutput.compensation_philosophy },
      { key: 'trajectory_mastery', name: 'Trajectory & Growth', data: crewOutput.trajectory_mastery },
      { key: 'north_star', name: 'North Star Alignment', data: crewOutput.north_star },
      { key: 'values_compass', name: 'Values Alignment', data: crewOutput.values_compass },
      { key: 'lifestyle_alignment', name: 'Lifestyle Fit', data: crewOutput.lifestyle_alignment },
      { key: 'purpose_impact', name: 'Purpose & Impact', data: crewOutput.purpose_impact },
      { key: 'industry_focus', name: 'Industry Focus', data: crewOutput.industry_focus },
      { key: 'company_filters', name: 'Company Culture', data: crewOutput.company_filters },
    ];

    return dimensions
      .filter(dim => dim.data?.score && dim.data.score < 3)
      .map(dim => ({
        name: dim.name,
        score: dim.data.score,
        explanation: dim.data.readable_explanation,
        isPositive: false
      }))
      .sort((a, b) => (a.score || 0) - (b.score || 0)); // Sort by score asc (most concerning first)
  };

  // Extract context dimensions
  const getContextDimensions = () => {
    const dimensions = [
      { key: 'industry_focus', name: 'Industry Position', data: crewOutput.industry_focus },
      { key: 'company_filters', name: 'Company Culture', data: crewOutput.company_filters },
      { key: 'purpose_impact', name: 'Purpose Alignment', data: crewOutput.purpose_impact },
    ];

    return dimensions
      .filter(dim => dim.data?.score === 4 || dim.data?.score === 3) // Neutral/context info
      .map(dim => ({
        name: dim.name,
        score: dim.data.score,
        explanation: dim.data.readable_explanation,
        isPositive: dim.data.score === 4
      }));
  };

  const positiveDimensions = getPositiveDimensions();
  const concerningDimensions = getConcerningDimensions();
  const contextDimensions = getContextDimensions();

  return (
    <div className="space-y-4 w-full">
      {/* Key Strengths - High Priority */}
      <SummaryCard
        title="Key Strengths"
        icon="✅"
        priority="high"
        dimensions={positiveDimensions}
        defaultExpanded={true}
      />

      {/* Important Considerations - Medium Priority */}
      <SummaryCard
        title="Important Considerations"
        icon="🤔"
        priority="medium"
        dimensions={concerningDimensions}
        defaultExpanded={false}
      />

      {/* Additional Context - Low Priority */}
      <SummaryCard
        title="Additional Context"
        icon="ℹ️"
        priority="low"
        dimensions={contextDimensions}
        defaultExpanded={false}
      />

      {/* Show message if no analysis available */}
      {positiveDimensions.length === 0 && concerningDimensions.length === 0 && contextDimensions.length === 0 && (
        <div className="text-center py-8 text-slate-500 dark:text-slate-400">
          <p className="text-sm">Career brand analysis not yet available</p>
          <p className="text-xs mt-1">Analysis will appear once AI review is completed</p>
        </div>
      )}
    </div>
  );
}

export default CareerBrandSummary;

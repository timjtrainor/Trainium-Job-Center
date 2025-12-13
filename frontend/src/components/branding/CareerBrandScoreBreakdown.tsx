"use client";

import React from 'react';
import { ChevronUpDownIcon, ClockIcon } from '../shared/ui/IconComponents';

interface CareerBrandScoreBreakdownProps {
  crewOutput: {
    constraints?: {
      overall_alignment_score?: number;
      score?: number;
    };
    compensation_philosophy?: {
      overall_alignment_score?: number;
      score?: number;
    };
    trajectory_mastery?: {
      overall_alignment_score?: number;
      score?: number;
    };
    north_star?: {
      overall_alignment_score?: number;
      score?: number;
    };
    values_compass?: {
      overall_alignment_score?: number;
      score?: number;
    };
    lifestyle_alignment?: {
      overall_alignment_score?: number;
      score?: number;
    };
    purpose_impact?: {
      overall_alignment_score?: number;
      score?: number;
    };
    industry_focus?: {
      overall_alignment_score?: number;
      score?: number;
    };
    company_filters?: {
      overall_alignment_score?: number;
      score?: number;
    };
  };
  overallScore?: number;
}

interface ScoreBreakdownBarProps {
  dimension: string;
  score: number;
  weight: number;
  contribution: number;
  isHighest?: boolean;
}

function ScoreBreakdownBar(props: ScoreBreakdownBarProps) {
  const { dimension, score, weight, contribution, isHighest = false } = props;
  const [isExpanded, setIsExpanded] = React.useState(false);

  const getScoreColor = (score: number) => {
    if (score >= 8.5) return 'bg-green-500';
    if (score >= 7.5) return 'bg-green-400';
    if (score >= 6.5) return 'bg-blue-400';
    if (score >= 5.5) return 'bg-yellow-400';
    if (score >= 4.5) return 'bg-orange-400';
    return 'bg-red-400';
  };

  return (
    <div className={`${isHighest ? 'ring-2 ring-blue-300 dark:ring-blue-600 rounded-lg p-3 mb-2' : 'mb-1'}`}>
      <div className="flex items-center justify-between text-sm mb-1">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-medium px-2 py-0.5 rounded ${
            isHighest
              ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
              : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
          }`}>
            {weight}% weight
          </span>
          <span className="font-medium text-slate-900 dark:text-slate-100">
            {dimension}
          </span>
        </div>
        <div className="text-right">
          <div className="font-semibold text-slate-900 dark:text-slate-100">
            {score.toFixed(1)}/5
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-400">
            {(score/5).toFixed(1)} × {weight}% = {contribution.toFixed(1)}
          </div>
        </div>
      </div>

      {/* Visual Bar */}
      <div className="relative w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${getScoreColor(contribution)} transition-all duration-300`}
          style={{ width: `${(contribution / 2) * 100}%` }} // Max contribution is ~2.5, so *40 gives reasonable bar width
        ></div>
        {/* Weight indicator on bar */}
        <div
          className="absolute top-0 h-full border-r-2 border-dashed border-slate-400 dark:border-slate-500"
          style={{ left: `${weight * 0.8}%` }}
          title={`Weight: ${weight}%`}
        ></div>
      </div>

      {/* Expandable details */}
      <div className="mt-1">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 flex items-center gap-1"
        >
          <ChevronUpDownIcon className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          {isExpanded ? 'Less details' : 'More details'}
        </button>

        {isExpanded && (
          <div className="mt-2 text-xs text-slate-600 dark:text-slate-400 space-y-1">
            <div>• Raw score: {score.toFixed(1)}/5</div>
            <div>• Converted to 0-10 scale: {(score - 1) * 2.5}</div>
            <div>• Applied {(weight/100).toFixed(2)} weight: {(score - 1) * 2.5 * (weight/100)}</div>
            <div>• Contributes {contribution.toFixed(1)} to final score</div>
          </div>
        )}
      </div>
    </div>
  );
}

export function CareerBrandScoreBreakdown({ crewOutput, overallScore }: CareerBrandScoreBreakdownProps) {
  // Define dimension priorities and weights (matches the orchestrator logic)
  const dimensionConfig = [
    { key: 'constraints', name: 'Hard Requirements', weight: 25 },
    { key: 'compensation_philosophy', name: 'Compensation Philosophy', weight: 20 },
    { key: 'trajectory_mastery', name: 'Trajectory & Mastery', weight: 18 },
    { key: 'north_star', name: 'North Star & Vision', weight: 15 },
    { key: 'values_compass', name: 'Values Compass', weight: 10 },
    { key: 'lifestyle_alignment', name: 'Lifestyle Alignment', weight: 8 },
    { key: 'purpose_impact', name: 'Purpose & Impact', weight: 3 },
    { key: 'industry_focus', name: 'Industry Focus', weight: 1 },
    { key: 'company_filters', name: 'Company Culture', weight: 0 },
  ];

  const calculateDimensionsData = () => {
    return dimensionConfig.map(dim => {
      const data = crewOutput[dim.key as keyof typeof crewOutput];
      if (!data || data.score === undefined) {
        return {
          key: dim.key,
          name: dim.name,
          weight: dim.weight,
          score: 0,
          contribution: 0
        };
      }

      // Convert 1-5 score to 0-10 scale and apply weight
      const score = data.score;
      const normalizedScore = (score - 1) * 2.5; // Convert 1→0, 5→10
      const weightMultiplier = dim.weight / 100;
      const contribution = normalizedScore * weightMultiplier;

      return {
        key: dim.key,
        name: dim.name,
        weight: dim.weight,
        score: score,
        contribution: contribution
      };
    });
  };

  const dimensionsData = calculateDimensionsData();
  const maxContribution = Math.max(...dimensionsData.map(d => d.contribution));
  const topContributor = dimensionsData.find(d => d.contribution === maxContribution);

  return (
    <div className="bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
        <ClockIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        Alignment Score Breakdown
      </h3>

      {/* Overall Score Summary */}
      <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-semibold text-blue-900 dark:text-blue-100">Overall Alignment Score</h4>
            <p className="text-sm text-blue-700 dark:text-blue-200">
              Weighted average across 9 career dimensions
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-blue-900 dark:text-blue-100">
              {overallScore?.toFixed(1) || '--'}/10
            </div>
            <div className="text-xs text-blue-600 dark:text-blue-300">
              {(overallScore ? (overallScore / 10 * 100).toFixed(1) : '--')}% alignment
            </div>
          </div>
        </div>
      </div>

      {/* Top Contributor Highlight */}
      {topContributor && topContributor.score > 0 && (
        <div className="mb-4 p-3 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <h4 className="font-semibold text-green-800 dark:text-green-200 text-sm mb-1">🏆 Highest Contributor</h4>
          <p className="text-sm text-green-700 dark:text-green-300">
            <strong>{topContributor.name}</strong> contributes the most
            ({topContributor.contribution.toFixed(1)} points) to your overall score
          </p>
        </div>
      )}

      {/* Dimension Breakdown */}
      <div className="space-y-2">
        <h4 className="font-semibold text-slate-900 dark:text-slate-100 text-sm mb-3">
          Individual Dimension Contributions
        </h4>

        {dimensionsData.map((dimensionData, index) => {
          // Explicit destructuring to avoid prop confusion
          const dimensionName = dimensionData.name;
          const dimensionScore = dimensionData.score;
          const dimensionWeight = dimensionData.weight;
          const dimensionContribution = dimensionData.contribution;
          const isHighestContributor = dimensionContribution === topContributor?.contribution;

          return (
            <React.Fragment key={`score-breakdown-${dimensionData.key}-${index}`}>
              <ScoreBreakdownBar
                dimension={dimensionName}
                score={dimensionScore}
                weight={dimensionWeight}
                contribution={dimensionContribution}
                isHighest={isHighestContributor}
              />
            </React.Fragment>
          );
        })}
      </div>

      {/* Methodology Note */}
      <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          <strong>How it works:</strong> Each dimension is scored 1-5, converted to a 0-10 scale,
          then weighted by importance. The weighted scores are summed to create your overall
          alignment score.
        </p>
      </div>
    </div>
  );
}

export default CareerBrandScoreBreakdown;

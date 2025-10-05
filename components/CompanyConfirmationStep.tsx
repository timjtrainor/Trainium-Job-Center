import React, { useEffect, useMemo, useState } from 'react';
import { Company } from '../types';
import { PlusCircleIcon, LoadingSpinner, SparklesIcon } from './IconComponents';

type CompanyDetailModalOptions = {
  autoResearch?: boolean;
  homepageUrl?: string;
  onResearchComplete?: (status: 'completed' | 'failed') => void;
};

interface CompanyConfirmationStepProps {
  initialCompanyName: string;
  allCompanies: Company[];
  onConfirm: (companyId: string) => void;
  onOpenCreateCompanyModal: (initialData: { company_name: string }) => void;
  onOpenCompanyDetailModal?: (companyId: string, options?: CompanyDetailModalOptions) => void;
  isLoading: boolean;
}

export const CompanyConfirmationStep = ({
  initialCompanyName,
  allCompanies,
  onConfirm,
  onOpenCreateCompanyModal,
  onOpenCompanyDetailModal,
  isLoading
}: CompanyConfirmationStepProps): React.ReactNode => {
  const matchingCompanies = useMemo(() => {
    if (!initialCompanyName) return [];
    const lowerCaseName = initialCompanyName.toLowerCase();
    return allCompanies.filter(c => c.company_name.toLowerCase().includes(lowerCaseName));
  }, [initialCompanyName, allCompanies]);

  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(
    matchingCompanies.length > 0 ? matchingCompanies[0].company_id : null
  );
  const [aiResearchStatus, setAiResearchStatus] = useState<'not_run' | 'running' | 'completed' | 'failed'>('not_run');
  const [companyHomepageUrl, setCompanyHomepageUrl] = useState<string>('');

  // Function to check if company has research data saved locally
  const checkResearchStatus = (selectedCompany: Company): boolean => {
    return !!(selectedCompany.mission?.text || selectedCompany.values?.text ||
              selectedCompany.goals?.text || selectedCompany.issues?.text ||
              selectedCompany.customer_segments?.text || selectedCompany.strategic_initiatives?.text);
  };

  // Update research status whenever the selected company data changes
  useEffect(() => {
    if (!selectedCompanyId) {
      setAiResearchStatus('not_run');
      setCompanyHomepageUrl('');
      return;
    }

    const selectedCompany = allCompanies.find(c => c.company_id === selectedCompanyId);
    if (!selectedCompany) {
      setAiResearchStatus('not_run');
      return;
    }

    if (aiResearchStatus !== 'running') {
      setCompanyHomepageUrl(selectedCompany.company_url || '');
    }

    const hasAiResearch = checkResearchStatus(selectedCompany);
    setAiResearchStatus(prevStatus => {
      if (prevStatus === 'running' && !hasAiResearch) {
        return 'running';
      }
      return hasAiResearch ? 'completed' : 'not_run';
    });
  }, [selectedCompanyId, allCompanies, aiResearchStatus]);

  const runCompanyAiResearch = async () => {
    if (!selectedCompanyId || !onOpenCompanyDetailModal) return;

    setAiResearchStatus('running');

    onOpenCompanyDetailModal(selectedCompanyId, {
      autoResearch: true,
      homepageUrl: companyHomepageUrl || undefined,
      onResearchComplete: (status) => {
        setAiResearchStatus(status);
      }
    });
  };

  // Function to ensure company data is loaded before confirmation
  const ensureCompanyDataLoaded = (): boolean => {
    if (!selectedCompanyId) return false;

    const selectedCompany = allCompanies.find(c => c.company_id === selectedCompanyId);
    if (!selectedCompany) return false;

    // Check if company has research data by looking at local data
    return checkResearchStatus(selectedCompany);
  };

  // Enhanced confirmation handler with company data verification
  const handleConfirmation = () => {
    if (!selectedCompanyId) return;

    const selectedCompany = allCompanies.find(c => c.company_id === selectedCompanyId);
    if (!selectedCompany) return;

    // Verify company data is available (has AI research)
    const hasCompanyData = ensureCompanyDataLoaded();

    if (!hasCompanyData) {
      // If no company data after checking, show warning but allow continuation
      console.warn('Company data may not be loaded, but proceeding with confirmation');
    }

    // Proceed with job analysis
    onConfirm(selectedCompanyId);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 3: Confirm Company</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          The AI identified the company as "{initialCompanyName}". Please select an existing company record or create a new one.
        </p>

        {/* AI Company Research Status */}
        {selectedCompanyId && (
          <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <SparklesIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div className="flex-1">
                  <h3 className="font-semibold text-slate-900 dark:text-white">Company AI Research</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {aiResearchStatus === 'completed' && '✅ AI research completed - company profile available'}
                    {aiResearchStatus === 'running' && '🔄 Running AI research on company...'}
                    {aiResearchStatus === 'not_run' && '❌ AI research not run yet'}
                    {aiResearchStatus === 'failed' && '❌ AI research failed - try again'}
                  </p>
                  {/* Homepage URL Input */}
                  {aiResearchStatus !== 'completed' && aiResearchStatus !== 'running' && (
                    <div className="mt-2">
                      <label htmlFor="company-homepage-url" className="block text-xs font-medium text-slate-600 dark:text-slate-400">
                        Company Homepage URL (for better research results)
                      </label>
                      <input
                        type="url"
                        id="company-homepage-url"
                        value={companyHomepageUrl}
                        onChange={(e) => setCompanyHomepageUrl(e.target.value)}
                        placeholder="https://www.company.com"
                        className="mt-1 block w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  )}
                </div>
              </div>
              <div className="flex flex-col gap-2">
                {aiResearchStatus !== 'completed' && aiResearchStatus !== 'running' && (
                  <button
                    onClick={runCompanyAiResearch}
                    disabled={isLoading}
                    className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100 dark:hover:bg-blue-900/50 disabled:opacity-50"
                  >
                    <SparklesIcon className="h-4 w-4" />
                    Run AI Research
                  </button>
                )}
                {aiResearchStatus === 'completed' && onOpenCompanyDetailModal && (
                  <button
                    onClick={() => onOpenCompanyDetailModal(selectedCompanyId!, { homepageUrl: companyHomepageUrl || undefined })}
                    disabled={isLoading}
                    className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/30 hover:bg-green-100 dark:hover:bg-green-900/50 disabled:opacity-50"
                  >
                    <SparklesIcon className="h-4 w-4" />
                    View Company Intelligence
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {matchingCompanies.length > 0 && (
          <div>
            <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">Potential Matches</h3>
            <div className="mt-2 space-y-2 max-h-48 overflow-y-auto pr-2">
              {matchingCompanies.map(company => (
                <label
                  key={company.company_id}
                  className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedCompanyId === company.company_id
                      ? 'bg-blue-50 border-blue-300 dark:bg-blue-900/30 dark:border-blue-700'
                      : 'bg-white hover:bg-slate-50 border-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700/50 dark:border-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="company-selection"
                    value={company.company_id}
                    checked={selectedCompanyId === company.company_id}
                    onChange={() => {
                      setSelectedCompanyId(company.company_id);
                      setCompanyHomepageUrl(company.company_url || '');
                      setAiResearchStatus(checkResearchStatus(company) ? 'completed' : 'not_run');
                    }}
                    className="h-4 w-4 border-slate-300 text-blue-600 focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <div className="ml-3 text-sm">
                    <p className="font-medium text-slate-900 dark:text-white">{company.company_name}</p>
                    <p className="text-slate-500 dark:text-slate-400">{company.company_url || 'No URL on record'}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        <div>
          <button
            type="button"
            onClick={() => onOpenCreateCompanyModal({ company_name: initialCompanyName })}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 p-3 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors disabled:opacity-50"
          >
            <PlusCircleIcon className="h-5 w-5" />
            Create New Company Record
          </button>
        </div>
      </div>

      <div className="flex items-center justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={handleConfirmation}
          disabled={!selectedCompanyId || isLoading || aiResearchStatus === 'running'}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400 disabled:cursor-not-allowed"
        >
          {isLoading ? <LoadingSpinner /> :
           aiResearchStatus === 'running' ? 'Company Research In Progress...' :
           'Confirm and Analyze Job'}
        </button>
      </div>
    </div>
  );
};

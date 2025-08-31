import React, { useState, useMemo } from 'react';
import { Company } from '../types';
import { PlusCircleIcon, LoadingSpinner } from './IconComponents';

interface CompanyConfirmationStepProps {
  initialCompanyName: string;
  allCompanies: Company[];
  onConfirm: (companyId: string) => void;
  onOpenCreateCompanyModal: (initialData: { company_name: string }) => void;
  isLoading: boolean;
}

export const CompanyConfirmationStep = ({
  initialCompanyName,
  allCompanies,
  onConfirm,
  onOpenCreateCompanyModal,
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

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Step 3: Confirm Company</h2>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          The AI identified the company as "{initialCompanyName}". Please select an existing company record or create a new one.
        </p>
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
                    onChange={() => setSelectedCompanyId(company.company_id)}
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
          onClick={() => selectedCompanyId && onConfirm(selectedCompanyId)}
          disabled={!selectedCompanyId || isLoading}
          className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400 disabled:cursor-not-allowed"
        >
          {isLoading ? <LoadingSpinner /> : 'Confirm and Analyze Job'}
        </button>
      </div>
    </div>
  );
};
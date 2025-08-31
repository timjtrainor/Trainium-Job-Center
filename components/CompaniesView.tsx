

import React, { useState, useMemo } from 'react';
import { Company, JobApplication } from '../types';
import { CompanyIcon, ArrowRightIcon, PlusCircleIcon } from './IconComponents';

interface CompaniesViewProps {
  companies: Company[];
  applications: JobApplication[];
  onViewCompany: (companyId: string) => void;
  onAddNewCompany: () => void;
}

export const CompaniesView = ({ companies, applications, onViewCompany, onAddNewCompany }: CompaniesViewProps): React.ReactNode => {
    const [searchTerm, setSearchTerm] = useState('');

    const appCountByCompany = useMemo(() => {
        const counts = new Map<string, number>();
        applications.forEach(app => {
            counts.set(app.company_id, (counts.get(app.company_id) || 0) + 1);
        });
        return counts;
    }, [applications]);

    const filteredCompanies = useMemo(() => {
        return companies.filter(c => c.company_name.toLowerCase().includes(searchTerm.toLowerCase()));
    }, [companies, searchTerm]);

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Elements</h1>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">Research and track the elemental data of each company.</p>
                </div>
                 <button
                    onClick={onAddNewCompany}
                    className="inline-flex items-center justify-center w-full md:w-auto px-5 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                    <PlusCircleIcon className="w-5 h-5 mr-2 -ml-1" />
                    Create New Company
                </button>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-slate-200 dark:border-slate-700">
                <div className="mb-4">
                     <label htmlFor="search-companies" className="sr-only">Search Companies</label>
                    <input
                        type="text"
                        id="search-companies"
                        placeholder="Search by company name..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full max-w-sm rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredCompanies.map(company => (
                        <div 
                            key={company.company_id} 
                            className="group bg-slate-50 dark:bg-slate-800/80 p-4 rounded-lg border border-slate-200 dark:border-slate-700 flex flex-col justify-between hover:border-blue-400 dark:hover:border-blue-500 transition-colors cursor-pointer"
                            onClick={() => onViewCompany(company.company_id)}
                        >
                            <div className="flex items-center">
                                <div className="flex-shrink-0 bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 rounded-lg p-3">
                                    <CompanyIcon className="h-6 w-6" />
                                </div>
                                <div className="ml-4 flex-1 overflow-hidden">
                                    <h3 className="font-bold text-lg text-blue-700 dark:text-blue-400 truncate">{company.company_name}</h3>
                                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                        {appCountByCompany.get(company.company_id) || 0} application(s)
                                    </p>
                                </div>
                            </div>
                            <div className="mt-4 flex justify-end">
                                <span className="inline-flex items-center text-sm font-medium text-blue-600 group-hover:text-blue-500 dark:text-blue-400 dark:group-hover:text-blue-300">
                                    View Details <ArrowRightIcon className="h-4 w-4 ml-1" />
                                </span>
                            </div>
                        </div>
                    ))}
                     {companies.length === 0 && (
                        <p className="text-center py-10 text-slate-500 dark:text-slate-400 col-span-full">
                            No companies found. They will appear here as you create applications.
                        </p>
                    )}
                    {companies.length > 0 && filteredCompanies.length === 0 && (
                        <p className="text-center py-10 text-slate-500 dark:text-slate-400 col-span-full">
                           No companies match your search.
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
};
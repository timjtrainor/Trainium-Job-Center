import React, { useState, useMemo } from 'react';
import { JobApplication, Status, Company, StrategicNarrative } from '../types';
import { TrashIcon } from './IconComponents';
import { Switch } from './Switch';

interface ApplicationsTableProps {
  title: string;
  applications: JobApplication[];
  companies: Company[];
  statuses: Status[];
  strategicNarratives: StrategicNarrative[];
  onViewApplication: (appId: string) => void;
  onViewCompany: (companyId: string) => void;
  onUpdateApplicationStatus: (appId: string, statusId: string) => Promise<void>;
  onDeleteApplication?: (appId: string) => void;
}

const getStatusClassName = (statusName: string) => {
  const baseClass = "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset";
  const statusMap: { [key: string]: string } = {
    'Step-1: Job loaded': 'bg-gray-50 text-gray-600 ring-gray-500/10 dark:bg-gray-400/10 dark:text-gray-400 dark:ring-gray-400/20',
    'Step-2: Approved by Applicant': 'bg-cyan-50 text-cyan-700 ring-cyan-600/20 dark:bg-cyan-400/10 dark:text-cyan-400 dark:ring-cyan-400/20',
    'Step-3: Resume created': 'bg-sky-50 text-sky-700 ring-sky-600/20 dark:bg-sky-400/10 dark:text-sky-400 dark:ring-sky-400/20',
    'Step-4: Applied': 'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20',
    'Step-5: Comment/DM created': 'bg-lime-50 text-lime-700 ring-lime-600/20 dark:bg-lime-400/10 dark:text-lime-400 dark:ring-lime-400/20',
    'Step-6: Email sent waiting for follow-up': 'bg-purple-50 text-purple-700 ring-purple-600/20 dark:bg-purple-400/10 dark:text-purple-400 dark:ring-purple-400/20',
    'Bad Fit': 'bg-orange-50 text-orange-700 ring-orange-600/20 dark:bg-orange-400/10 dark:text-orange-400 dark:ring-orange-400/20',
    'Rejected': 'bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-400/10 dark:text-red-400 dark:ring-red-400/20',
    'Hold': 'bg-yellow-50 text-yellow-800 ring-yellow-600/20 dark:bg-yellow-400/10 dark:text-yellow-500 dark:ring-yellow-400/20',
    'Waiting': 'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20',
    'Interviewing': 'bg-blue-50 text-blue-700 ring-blue-700/10 font-bold dark:bg-blue-400/10 dark:text-blue-300 dark:ring-blue-400/30',
    'Accepted': 'bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-500/20',
    'AI Generated': 'bg-indigo-50 text-indigo-700 ring-indigo-600/20 dark:bg-indigo-400/10 dark:text-indigo-300 dark:ring-indigo-400/20',
    'Draft': 'bg-slate-50 text-slate-700 ring-slate-600/20 dark:bg-slate-500/10 dark:text-slate-300 dark:ring-slate-500/20',
  };
  return `${baseClass} ${statusMap[statusName] || 'bg-gray-50 text-gray-600 ring-gray-500/10'}`;
};


export const ApplicationsTable = ({ title, applications, companies, statuses, strategicNarratives, onViewApplication, onViewCompany, onUpdateApplicationStatus, onDeleteApplication }: ApplicationsTableProps): React.ReactNode => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showRejected, setShowRejected] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState<string | null>(null);

  const companyMap = useMemo(() => new Map(companies.map(c => [c.company_id, c.company_name])), [companies]);
  const narrativeMap = useMemo(() => new Map(strategicNarratives.map(n => [n.narrative_id, n.narrative_name])), [strategicNarratives]);

  const filteredAndSortedApplications = useMemo(() => {
    const statusSortOrder: Record<string, number> = {
        'Interviewing': 1,
        'Step-3: Resume created': 2,
        'AI Generated': 3,
        'Draft': 4,
        'Accepted': 5,
        'Step-6: Email sent waiting for follow-up': 6,
        'Step-5: Comment/DM created': 7,
        'Step-4: Applied': 8,
        'Waiting': 9,
        'Hold': 10,
        'Step-2: Approved by Applicant': 11,
        'Step-1: Job loaded': 12,
        'Bad Fit': 13,
        'Rejected': 14,
    };

    const workflowSortOrder: Record<string, number> = {
        'fast_track': 1,
        'ai_generated': 2,
        'manual': 3,
    };

    const getSortKey = (statusName: string | undefined): number => {
        if (!statusName) {
            return 10;
        }
        return statusSortOrder[statusName] || 99;
    };

    const processedApps = applications
      .filter(app => {
        const lowerSearch = searchTerm.toLowerCase();
        const companyName = companyMap.get(app.company_id)?.toLowerCase() || '';
        const jobTitle = app.job_title.toLowerCase();
        const narrativeName = narrativeMap.get(app.narrative_id)?.toLowerCase() || '';
        
        const matchesSearch = searchTerm ? 
            companyName.includes(lowerSearch) || 
            jobTitle.includes(lowerSearch) ||
            narrativeName.includes(lowerSearch)
            : true;

        const matchesStatus = statusFilter !== 'all' ? app.status?.status_name === statusFilter : true;
        
        const matchesRejection = showRejected ? true : app.status?.status_name !== 'Rejected' && app.status?.status_name !== 'Bad Fit';

        return matchesSearch && matchesStatus && matchesRejection;
      })
      .sort((a, b) => {
        const sortKeyA = getSortKey(a.status?.status_name);
        const sortKeyB = getSortKey(b.status?.status_name);
        if (sortKeyA !== sortKeyB) {
          return sortKeyA - sortKeyB;
        }
        const workflowKeyA = workflowSortOrder[a.workflow_mode || ''] || 99;
        const workflowKeyB = workflowSortOrder[b.workflow_mode || ''] || 99;
        if (workflowKeyA !== workflowKeyB) {
          return workflowKeyA - workflowKeyB;
        }
        // Then by date applied
        return new Date(b.date_applied).getTime() - new Date(a.date_applied).getTime();
      });

    return processedApps;
  }, [applications, searchTerm, statusFilter, showRejected, companyMap, narrativeMap]);

  const uniqueStatuses = useMemo(() => Array.from(new Set(applications.map(app => app.status?.status_name).filter(Boolean))), [applications]);

  const getWorkflowLabel = (mode?: string) => {
    switch (mode) {
      case 'fast_track':
        return 'Fast Track';
      case 'ai_generated':
        return 'AI Generated';
      case 'manual':
        return 'Manual AI';
      default:
        return 'Manual AI';
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
      <div className="p-4 sm:p-6 border-b border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">{title}</h2>
        <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="w-full sm:w-1/2">
                <input
                    type="text"
                    placeholder="Search by title, company, or narrative..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
            </div>
             <div className="flex items-center gap-4 w-full sm:w-auto">
                 <div className="flex items-center">
                    <Switch enabled={showRejected} onChange={setShowRejected} />
                    <span className="ml-2 text-sm font-medium text-slate-700 dark:text-slate-300">Show Rejected</span>
                 </div>
                 <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full sm:w-auto rounded-md border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                    <option value="all">All Statuses</option>
                    {uniqueStatuses.map(status => (
                        <option key={status} value={status}>{status}</option>
                    ))}
                </select>
            </div>
        </div>
      </div>
      <div className="-mx-4 sm:-mx-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
            <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                    <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-white sm:pl-6">Job</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Narrative</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Status</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Workflow</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Applied</th>
                    <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6"><span className="sr-only">Actions</span></th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-slate-700 bg-white dark:bg-slate-800">
                {filteredAndSortedApplications.map(app => (
                    <tr key={app.job_application_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 group">
                        <td className="py-4 pl-4 pr-3 text-sm sm:pl-6 cursor-pointer" onClick={() => onViewApplication(app.job_application_id)}>
                            <div className="font-medium text-gray-900 dark:text-white">{app.job_title}</div>
                            <div 
                                className="text-gray-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:underline"
                                onClick={(e) => { e.stopPropagation(); onViewCompany(app.company_id); }}
                            >
                                {companyMap.get(app.company_id)}
                            </div>
                        </td>
                        <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400 cursor-pointer" onClick={() => onViewApplication(app.job_application_id)}>{narrativeMap.get(app.narrative_id) || 'N/A'}</td>
                        <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400" onClick={(e) => e.stopPropagation()}>
                            {(() => {
                                const currentStatus = statuses.find(status => status.status_id === app.status?.status_id);
                                const wrapperClass = getStatusClassName(currentStatus?.status_name || 'Unknown');
                                return (
                                    <div className={`${wrapperClass} cursor-pointer transition hover:ring-2 hover:ring-blue-400 dark:hover:ring-blue-300 focus-within:ring-2 focus-within:ring-blue-500`}
                                        style={{ padding: 0 }}
                                    >
                                        <select
                                            value={app.status?.status_id || ''}
                                            onChange={async (event) => {
                                                const nextStatusId = event.target.value;
                                                if (!nextStatusId || nextStatusId === app.status?.status_id) {
                                                    return;
                                                }
                                                setStatusUpdating(app.job_application_id);
                                                try {
                                                    await onUpdateApplicationStatus(app.job_application_id, nextStatusId);
                                                } finally {
                                                    setStatusUpdating(null);
                                                }
                                            }}
                                            disabled={statusUpdating === app.job_application_id}
                                            className="bg-transparent border-none text-sm font-medium text-current px-2 py-1 pr-6 appearance-none focus:outline-none"
                                        >
                                            <option value="" disabled>Select status</option>
                                            {statuses.map(status => (
                                                <option key={status.status_id} value={status.status_id}>{status.status_name}</option>
                                            ))}
                                        </select>
                                    </div>
                                );
                            })()}
                        </td>
                        <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400 cursor-pointer" onClick={() => onViewApplication(app.job_application_id)}>{getWorkflowLabel(app.workflow_mode)}</td>
                        <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400 cursor-pointer" onClick={() => onViewApplication(app.job_application_id)}>{new Date(app.date_applied).toLocaleDateString()}</td>
                        <td className="py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                            {onDeleteApplication && <button onClick={(e) => { e.stopPropagation(); onDeleteApplication(app.job_application_id); }} className="p-1 text-slate-400 hover:text-red-500 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 opacity-0 group-hover:opacity-100 transition-opacity" title="Delete Application"><TrashIcon className="h-5 w-5"/></button>}
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
      </div>
    </div>
  );
};

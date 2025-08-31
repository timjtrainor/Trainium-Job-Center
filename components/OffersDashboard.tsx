import React from 'react';
import { Offer, JobApplication } from '../types';
import { TrashIcon } from './IconComponents';

interface OffersDashboardProps {
    offers: Offer[];
    applications: JobApplication[];
    onDeleteOffer: (offerId: string) => void;
}

const getStatusClassName = (status: Offer['status']) => {
    const baseClass = "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset";
    const statusMap: { [key: string]: string } = {
        'Received': 'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20',
        'Negotiating': 'bg-yellow-50 text-yellow-800 ring-yellow-600/20 dark:bg-yellow-400/10 dark:text-yellow-500 dark:ring-yellow-400/20',
        'Accepted': 'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20',
        'Declined': 'bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-400/10 dark:text-red-400 dark:ring-red-400/20',
    };
    return `${baseClass} ${statusMap[status] || 'bg-gray-50 text-gray-600 ring-gray-500/10'}`;
};

export const OffersDashboard = ({ offers, applications, onDeleteOffer }: OffersDashboardProps) => {
    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="p-4 sm:p-6 border-b border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Offer Comparison Dashboard</h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">View and compare all received offers side-by-side.</p>
            </div>
            <div className="-mx-4 sm:-mx-6 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead className="bg-slate-50 dark:bg-slate-800">
                        <tr>
                            <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-white sm:pl-6">Job</th>
                            <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Base Salary</th>
                            <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Bonus</th>
                            <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Equity</th>
                            <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Status</th>
                            <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6"><span className="sr-only">Actions</span></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-slate-700 bg-white dark:bg-slate-800">
                        {offers.map(offer => (
                            <tr key={offer.offer_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 group">
                                <td className="py-4 pl-4 pr-3 text-sm sm:pl-6">
                                    <div className="font-medium text-gray-900 dark:text-white">{offer.job_title}</div>
                                    <div className="text-gray-500 dark:text-slate-400">{offer.company_name}</div>
                                </td>
                                <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400 font-semibold">{offer.base_salary ? `$${Number(offer.base_salary).toLocaleString()}` : 'N/A'}</td>
                                <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400">{offer.bonus_potential || 'N/A'}</td>
                                <td className="px-3 py-4 text-sm text-gray-500 dark:text-slate-400">{offer.equity_details || 'N/A'}</td>
                                <td className="px-3 py-4 text-sm"><span className={getStatusClassName(offer.status)}>{offer.status}</span></td>
                                <td className="py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                                    <button onClick={(e) => { e.stopPropagation(); onDeleteOffer(offer.offer_id); }} className="p-1 text-slate-400 hover:text-red-500 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 opacity-0 group-hover:opacity-100 transition-opacity" title="Delete Offer"><TrashIcon className="h-5 w-5"/></button>
                                </td>
                            </tr>
                        ))}
                         {offers.length === 0 && (
                            <tr><td colSpan={6} className="text-center py-10 text-slate-500">No offers have been logged yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
import React from 'react';
import { useLocation } from 'react-router-dom';
import { UserPlusIcon } from './IconComponents';
import { Contact, Company, JobApplication } from '../types';

interface QuickContactButtonProps {
    onOpenContactModal: (contact: Partial<Contact>) => void;
    companies: Company[];
    applications: JobApplication[];
}

export const QuickContactButton: React.FC<QuickContactButtonProps> = ({
    onOpenContactModal,
    companies,
    applications
}) => {
    const location = useLocation();
    const path = location.pathname;

    const handleAddContact = () => {
        let initialContact: Partial<Contact> = {
            status: 'To Contact',
            date_contacted: new Date().toISOString().split('T')[0],
        };

        // Context-aware pre-filling
        if (path.startsWith('/application/')) {
            const appId = path.split('/')[2];
            const app = applications.find(a => a.job_application_id === appId);
            if (app) {
                initialContact.job_application_id = app.job_application_id;
                initialContact.company_id = app.company_id;
            }
        } else if (path.startsWith('/company/')) {
            const companyId = path.split('/')[2];
            const company = companies.find(c => c.company_id === companyId);
            if (company) {
                initialContact.company_id = company.company_id;
            }
        }

        onOpenContactModal(initialContact);
    };

    return (
        <button
            onClick={handleAddContact}
            className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition-transform hover:scale-110 hover:bg-blue-700 active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            title="Quick Add Contact"
        >
            <UserPlusIcon className="h-6 w-6" />
        </button>
    );
};

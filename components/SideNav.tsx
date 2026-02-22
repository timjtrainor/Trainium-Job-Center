import React from 'react';
import { NavLink } from 'react-router-dom';
import { LogoIcon, DashboardIcon, ApplicationsIcon, AtomGearIcon, ChatBubbleLeftRightIcon, StrategyIcon, MicrophoneIcon, UsersIcon, ClipboardDocumentListIcon, ClipboardDocumentCheckIcon, CircleStackIcon, ClockIcon, LinkIcon, NetworkingIcon } from './IconComponents';

interface SideNavProps {
    onOpenProfileModal: () => void;
    onOpenSprintModal: () => void;
}

type NavItem = {
    path: string;
    label: string;
    icon: React.ElementType;
    isModal?: boolean;
    end?: boolean;
}

const navItems: NavItem[] = [
    { path: '/', label: 'Dashboard', icon: DashboardIcon, end: true },
    { path: '/sprint', label: 'Sprint', icon: ClipboardDocumentListIcon, isModal: true },
    { path: '/positioning', label: 'Positioning', icon: StrategyIcon },
    { path: '/networking', label: 'Reaction Network', icon: NetworkingIcon },
    { path: '/engagement', label: 'Engagement Hub', icon: ChatBubbleLeftRightIcon },
    { path: '/reviewed-jobs', label: 'AI Job Board', icon: ClipboardDocumentCheckIcon },
    { path: '/applications', label: 'Application Lab', icon: ApplicationsIcon },
    { path: '/interview-studio', label: 'Interview Studio', icon: MicrophoneIcon },
    { path: '/brag-bank', label: 'Brag Bank', icon: ClipboardDocumentCheckIcon },
];

const secondaryNavItems = [
    { path: '/health-checks', label: 'Health Checks', icon: AtomGearIcon },
    { path: '/schedule-management', label: 'Job Scheduler', icon: ClockIcon },
    { path: '/webhook-management', label: 'Webhooks', icon: LinkIcon },
]

export const SideNav = ({ onOpenProfileModal, onOpenSprintModal }: SideNavProps): React.ReactNode => {

    const baseClass = "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors";
    const activeClass = "bg-blue-50 dark:bg-slate-800 text-blue-600 dark:text-blue-400 font-semibold";
    const inactiveClass = "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800";

    const iconBaseClass = "mr-3 flex-shrink-0 h-6 w-6 transition-colors";
    const iconActiveClass = "text-blue-500 dark:text-blue-400";
    const iconInactiveClass = "text-slate-400 dark:text-slate-500 group-hover:text-slate-500 dark:group-hover:text-slate-400";

    const renderNavLink = (item: NavItem) => {
        if (item.isModal) {
            return (
                <button
                    key={item.label}
                    onClick={item.label === 'Sprint' ? onOpenSprintModal : () => { }}
                    className={`${baseClass} w-full ${inactiveClass}`}
                >
                    <item.icon className={`${iconBaseClass} ${iconInactiveClass}`} />
                    <span>{item.label}</span>
                </button>
            );
        }

        return (
            <NavLink
                key={item.label}
                to={item.path}
                end={item.end}
                className={({ isActive }) => `${baseClass} w-full ${isActive ? activeClass : inactiveClass}`}
            >
                {({ isActive }) => (
                    <>
                        <item.icon className={`${iconBaseClass} ${isActive ? iconActiveClass : iconInactiveClass}`} />
                        <span>{item.label}</span>
                    </>
                )}
            </NavLink>
        );
    }


    return (
        <aside className="w-64 flex-shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col">
            <div className="flex items-center h-16 flex-shrink-0 px-4 space-x-3 border-b border-slate-200 dark:border-slate-800">
                <LogoIcon />
                <span className="font-bold text-slate-800 dark:text-slate-200 text-lg">Trainium</span>
            </div>
            <div className="flex-1 flex flex-col overflow-y-auto">
                <nav className="flex-1 px-2 py-4 space-y-1">
                    {navItems.map(renderNavLink)}
                </nav>
                <div className="px-2 py-4 border-t border-slate-200 dark:border-slate-800">
                    <div className="px-1 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        Dev Mode
                    </div>
                    <div className="space-y-1">
                        {secondaryNavItems.map(item => {
                            return (
                                <NavLink
                                    key={item.label}
                                    to={item.path}
                                    className={({ isActive }) => `${baseClass} w-full ${isActive ? activeClass : inactiveClass}`}
                                >
                                    {({ isActive }) => (
                                        <>
                                            <item.icon className={`${iconBaseClass} ${isActive ? iconActiveClass : iconInactiveClass}`} />
                                            <span>{item.label}</span>
                                        </>
                                    )}
                                </NavLink>
                            );
                        })}
                    </div>
                    <div className="mt-4">
                        <button
                            onClick={onOpenProfileModal}
                            className={`${baseClass} w-full ${inactiveClass}`}
                        >
                            <UsersIcon className={`${iconBaseClass} ${iconInactiveClass}`} />
                            <span>My Profile</span>
                        </button>
                    </div>
                </div>
            </div>
        </aside>
    );
};
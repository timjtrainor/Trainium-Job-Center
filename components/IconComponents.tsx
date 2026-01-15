import React from 'react';
import {
  CheckIcon,
  ArrowRightIcon,
  TagIcon,
  PlusCircleIcon,
  PlusIcon,
  UsersIcon,
  ChevronUpDownIcon,
  ChatBubbleLeftRightIcon,
  TrashIcon,
  EyeIcon,
  SparklesIcon,
  ArrowDownTrayIcon,
  LockClosedIcon,
  ArrowUturnLeftIcon,
  ArrowTopRightOnSquareIcon,
  DocumentTextIcon,
  LightBulbIcon,
  XCircleIcon,
  CheckBadgeIcon,
  ClockIcon,
  RocketLaunchIcon,
  MagnifyingGlassPlusIcon,
  MicrophoneIcon,
  CurrencyDollarIcon,
  ClipboardDocumentListIcon,
  ClipboardDocumentCheckIcon,
  CircleStackIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  HandThumbUpIcon as ThumbUpIcon,
  HandThumbDownIcon as ThumbDownIcon,
  InformationCircleIcon,
  TableCellsIcon,
  Squares2X2Icon,
  ClipboardDocumentIcon,
  XMarkIcon,
  GlobeAltIcon,
  MapPinIcon,
  CalendarIcon,
  Square2StackIcon,
  PaperAirplaneIcon,
  CubeIcon,
  BeakerIcon,
  DocumentDuplicateIcon,
  UserGroupIcon,
  BuildingOfficeIcon,
  BoltIcon,
  PencilSquareIcon,
  LinkIcon,
  ArrowTrendingUpIcon,
  ArrowPathIcon,
  HomeIcon,
  UserIcon,
  ChatBubbleBottomCenterTextIcon,
  ShieldCheckIcon,
  PresentationChartLineIcon,
  CloudArrowUpIcon,
  FlagIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

// --- Re-exports for Standard Heroicons ---
export {
  CheckIcon,
  ArrowRightIcon,
  TagIcon,
  PlusCircleIcon,
  PlusIcon,
  UsersIcon,
  ChevronUpDownIcon,
  ChatBubbleLeftRightIcon,
  TrashIcon,
  EyeIcon,
  SparklesIcon,
  ArrowDownTrayIcon,
  LockClosedIcon,
  ArrowUturnLeftIcon,
  ArrowTopRightOnSquareIcon,
  DocumentTextIcon,
  LightBulbIcon,
  XCircleIcon,
  CheckBadgeIcon,
  ClockIcon,
  RocketLaunchIcon,
  MagnifyingGlassPlusIcon,
  MicrophoneIcon,
  CurrencyDollarIcon,
  ClipboardDocumentListIcon,
  ClipboardDocumentCheckIcon,
  CircleStackIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ThumbUpIcon,
  ThumbDownIcon,
  InformationCircleIcon,
  TableCellsIcon,
  Squares2X2Icon,
  ClipboardDocumentIcon,
  XMarkIcon,
  GlobeAltIcon,
  MapPinIcon,
  CalendarIcon,
  Square2StackIcon,
  PaperAirplaneIcon,
  CubeIcon,
  BeakerIcon,
  DocumentDuplicateIcon,
  UserGroupIcon,
  BuildingOfficeIcon,
  BoltIcon,
  PencilSquareIcon,
  LinkIcon,
  ArrowTrendingUpIcon,
  ArrowPathIcon,
  HomeIcon,
  UserIcon,
  ChatBubbleBottomCenterTextIcon,
  ShieldCheckIcon,
  PresentationChartLineIcon,
  CloudArrowUpIcon,
  FlagIcon,
  ExclamationTriangleIcon
};

// --- Custom / Non-Heroicons ---

export const LogoIcon = ({
  className = "w-10 h-10",
  fillColor = "currentColor",
}: {
  className?: string;
  fillColor?: string;
}): React.ReactNode => (
  <svg className={className} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="40" height="40" rx="12" fill={fillColor} />
    <path d="M12 12L28 28M28 12L12 28" stroke="white" strokeWidth="4" strokeLinecap="round" />
  </svg>
);

export const LoadingSpinner = ({ className = "w-5 h-5" }: { className?: string }): React.ReactNode => (
  <svg className={`animate-spin ${className}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
);

export const GripVerticalIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5.25l.75 7.5-7.5.75" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 15l.75 7.5-7.5.75" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 5.25l-.75 7.5 7.5.75" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-.75 7.5 7.5.75" />
  </svg>
);

export const DashboardIcon = Squares2X2Icon;
export const ApplicationsIcon = Square2StackIcon;

export const AtomGearIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

export const StrategyIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18m9-9H3" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 7.5L12 12l4.5 4.5m-9-9L12 12l-4.5 4.5" />
  </svg>
);

export const NetworkingIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
    <circle cx="12" cy="12" r="3" />
    <circle cx="4" cy="4" r="2" />
    <circle cx="20" cy="4" r="2" />
    <circle cx="20" cy="20" r="2" />
    <circle cx="4" cy="20" r="2" />
    <path d="M6 6l4 4m4 4l4 4m0-12l-4 4m-4 4l-4 4" />
  </svg>
);

export const ResumeIcon = DocumentTextIcon;
export const CompanyIcon = BuildingOfficeIcon;

export const LinkedInIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 118.25 6.5 1.75 1.75 0 016.5 8.25zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.4 1.4 0 0013 13.19V19h-3v-9h2.9v1.3a3.11 3.11 0 012.7-1.4c1.55 0 3.36.96 3.36 4.66z" />
  </svg>
);

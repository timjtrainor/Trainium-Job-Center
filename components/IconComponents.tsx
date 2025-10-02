import React from 'react';

export const LogoIcon = ({
  className = "w-10 h-10",
  fillColor = "currentColor", // allows external override
}: {
  className?: string;
  fillColor?: string;
}): React.ReactNode => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 300 313"
    className={className}
    role="img"
    aria-label="Trainium Logo"
  >
    <g fill={fillColor}>
      {/* (Your existing <path> tags here, unchanged) */}
      {/* e.g. */}
      <path d="M98.3 2c-4.3 1-6.3 2.7-8 6.8-2.5 6.1 2.3 14.2 8.3 14.2h2.4v34.2c0 19.2-.4 35.8-1 37.8-1.2 4.5-7.1 14.7-28.7 50-9.7 15.7-23.2 37.7-30.1 49-6.9 11.3-16.8 27.5-22.2 36C1.8 257.6.5 261 1.2 274.1c.7 12.4 8.1 24.4 19.5 31.7 10.3 6.6 4 6.3 131.4 6l115.4-.3 4.8-2.2c11.5-5.3 21.1-15.4 24.9-26.1 3-8.7 2.3-20.6-1.8-29.2-1.7-3.6-14.6-24.9-28.6-47.5-14-22.6-30.6-49.3-36.8-59.5-6.2-10.2-14.1-23.1-17.6-28.7-12.4-20-12.7-20.6-13.6-36.4-.5-7.7-.7-24-.6-36.2l.3-22.1 3.5-.7c5-1 8-5 8-10.4 0-5.6-3-9.3-8.5-10.5C196.7.9 102.9.9 98.3 2zm82.9 56.7c.3 37.6.4 39 2.6 44.4 2.3 5.6 8 15.5 25.4 43.9 16 26 21.5 34.9 31.9 51 21.9 34.2 38 61.8 39.1 67.3 2.1 10-3.1 20.8-12 25l-4.7 2.2H36.4l-4.9-2.5c-9.2-4.8-14.3-15.9-11.6-25.9 1-3.6 14.9-28.2 23.6-41.8 1.1-1.7 4.6-7.3 7.9-12.5 3.2-5.1 6.9-10.9 8.1-12.8 1.3-1.9 7.1-11.4 13.1-21 5.9-9.6 14.8-24 19.7-32 17.4-28 22.8-37.6 24.7-43.9 1.8-5.8 2-9.3 2-43.2V20h61.9l.3 38.7z"/>
        <path d="M150.9 53.9c-3.6 3.6-3.7 7-.3 11 5.2 6.2 14.9 2.5 14.7-5.5-.2-7.8-8.8-11.1-14.4-5.5zm-13.4 37.3c-3.2 1.8-4.4 4-4.5 7.6 0 4.6 1.6 7.1 5.6 8.8 8.8 3.7 16.4-6.8 10.2-14.1-2.6-3-8.3-4.1-11.3-2.3zm7.2 44.6c-2.2 2.4-2.1 6.5.1 8.5 1.3 1.2 3.7 1.7 8.5 1.7 8.2 0 13.1 2.1 15.2 6.6 2 4.3 2 11.4 0 11.4-1 0-1.5 1.1-1.5 3.5 0 1.9.5 3.5 1 3.5.6 0 1 1.6 1 3.5v3.5h-31.9l-.3-3.8-.3-3.7h-24l-.3 3.7-.3 3.8H80.5l-4 6.2c-2.2 3.4-4.1 6.5-4.3 7-.2.4 4.8.8 11.2.8 11.3 0 11.6.1 11.7 2.2 0 1.3.2 3.1.4 4 .3 1.7-.9 1.8-13.9 1.8H67.5l-5.8 9.9c-3.1 5.4-8.1 13.6-11.1 18.2s-5.3 8.5-5.1 8.7c.2.2 28.3.5 62.4.6 59.1.1 62 .2 64 2 1.2 1.1 2.1 2.7 2.1 3.6 0 1.7-4 1.8-66.3 1.4-36.4-.1-66.7 0-67.2.4-1.6 1.1-6.5 8-6.5 9.1 0 .6 3.2 1.1 7.2 1.3l7.3.3.6 3.5c.3 1.9 1.1 4.5 1.7 5.7 2.2 4 1.6 4.3-9.3 4.3H31v6h113.5c99 0 113.6-.2 114.1-1.5.8-1.9-1.3-4.4-12.6-15-5.2-4.9-9.9-9.5-10.3-10.3-.5-.7-1.7-7.7-2.8-15.4-1.1-7.8-2.5-15-3.1-16.1-2.1-4-23.7-33.3-26.3-35.7-2.3-2.1-3.8-2.5-10.6-2.9l-7.9-.3v-3.4c0-1.9.5-3.4 1-3.4.6 0 1-1.3 1-2.9 0-2.3-.5-3-2.2-3.3-2.1-.3-2.3-.9-2.8-9-.5-7.6-.9-9.2-3.5-12.9-4.8-6.9-9.9-8.9-22-8.9-8.6 0-10.4.3-11.8 1.8zm-.4 58.9c1 5.4 1 5.4-19.7 5.1l-19.1-.3-.3-2.3c-.8-5.2-.6-5.2 19.7-5.2h18.9l.5 2.7zm29.2 6.3c3.2 5 5.8 9.9 5.9 10.8.1 1.5-1.3 1.7-11.6 2-6.5.1-11.9-.1-11.9-.5-.4-2.3-.6-19.9-.2-20.6.2-.4 3.1-.7 6.3-.7h5.8l5.7 9zm27.7-6.3c5.4 6 13.8 17.5 13.2 18.4-.3.5-4.2.9-8.8.9-6.6 0-8.6-.3-9.8-1.8-1.7-1.9-11.8-18.7-11.8-19.6 0-.3 3.3-.6 7.3-.6 6.7 0 7.5.2 9.9 2.7zm18.8 34.1c6.1 4.9-1.1 13.5-7.4 8.9-2.7-2-1.8-7.8 1.4-9.4 3.2-1.6 3.4-1.6 6 .5zM78.1 260c.4 2.5 1 5.5 1.4 6.7.7 2 .4 2.1-7.2 2.5-4.3.2-8.2 0-8.7-.4-.5-.3.1-1.9 1.3-3.4s2.4-4.5 2.7-6.6l.7-3.9 4.6.3 4.6.3.6 4.5zm31.1-4.4c4 .6 4.6 1 5.7 4 .7 1.9 2.3 4.2 3.7 5 1.3.9 2.4 2.3 2.4 3 0 1.1-2.8 1.4-14.1 1.4H92.8l2.1-3.4c1.2-1.8 2.1-4.7 2.1-6.3 0-1.6.3-3.3.7-3.6.8-.9 5.6-.9 11.5-.1zm50.4 2.1c.3 1.6 1.9 4.5 3.5 6.5s2.6 3.9 2.1 4.2c-1.2.7-20.1 1.1-20.8.3-.4-.3.5-2 2-3.7 1.4-1.8 2.9-4.4 3.3-5.8.8-3.4 1.9-4.2 6-4.2 2.7 0 3.4.4 3.9 2.7zm63.6 3.3c3.5 7.1 3.5 8.2.1 7.8-2.3-.2-3.4-1.4-5.8-6.1-2.6-4.9-2.8-5.9-1.5-6.7 2.7-1.8 4.5-.6 7.2 5zm14.8-.1c3.3 3.2 6 6.4 6 7 0 .8-1.5 1.1-4.2.9-4-.3-4.4-.6-7.1-5.7-2.5-4.6-3-8.1-1.2-8.1.3 0 3.2 2.6 6.5 5.9zm-101.6-3.3c1.8 4.8-.1 8.4-4.6 8.4-4.3 0-6.4-5.3-3.2-8.4 2-2.1 7-2.1 7.8 0zm44.4 2.8c.4 4.2-.8 5.6-4.5 5.6-3.9 0-5.9-6.9-2.5-8.9.9-.6 2.8-1 4.2-.8 2.1.2 2.5.8 2.8 4.1zm27.4 1.3c1.6 2.9 2.7 5.7 2.3 6.3-.7 1.2-22.5 1.4-22.5.2 0-.4 1.1-1.7 2.5-3 1.3-1.3 2.9-3.9 3.5-5.8 1.2-3.4 1.3-3.5 6.2-3.2 5 .3 5.1.4 8 5.5z"/>
      {/* ... etc. */}
    </g>
  </svg>
);


export const CheckIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
);

export const ArrowRightIcon = ({className = "h-5 w-5 ml-2"}: {className?: string}): React.ReactNode => (
     <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
    </svg>
);

export const LoadingSpinner = (): React.ReactNode => (
  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
);

export const PlusCircleIcon = ({className}: {className: string}): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

export const UsersIcon = ({ className, title }: { className: string; title?: string }): React.ReactNode => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 512 512"
    className={className}
    fill="currentColor"
    aria-hidden={title ? undefined : true}
    role="img"
  >
    {title && <title>{title}</title>}
    <path d="M256 0C114.613 0 0 114.616 0 255.996 0 397.382 114.613 512 256 512c141.386 0 256-114.617 256-256.004C512 114.616 397.387 0 256 0zm-.004 401.912c-69.247-.03-118.719-9.438-117.564-18.058 6.291-47.108 44.279-51.638 68.402-70.94 10.832-8.666 16.097-6.5 16.097-20.945v-23.111c-6.503-7.219-8.867-6.317-14.366-34.663-11.112 0-10.396-14.446-15.638-27.255-4.09-9.984-.988-14.294 2.443-16.165-1.852-9.87-.682-43.01 13.532-60.259l-2.242-15.649s4.47 1.121 15.646-1.122c11.181-2.227 38.004-8.93 53.654 4.477 37.557 5.522 47.53 36.368 40.204 72.326 3.598 1.727 7.178 5.962 2.901 16.392-5.238 12.809-4.522 27.255-15.634 27.255-5.496 28.346-7.863 27.444-14.366 34.663v23.111c0 14.445 5.261 12.279 16.093 20.945 24.126 19.301 62.111 23.831 68.406 70.94 1.151 8.62-48.318 18.028-117.568 18.058z" />
  </svg>
);

export const ChevronUpDownIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 15L12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9" />
    </svg>
);

export const ChatBubbleLeftRightIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={0.96}
    strokeMiterlimit={10}
    className={className}
    aria-hidden="true"
  >
    <circle cx="12" cy="12" r="1.91" />
    <path d="M9.14 16.77A2.86 2.86 0 0 1 12 13.91a2.86 2.86 0 0 1 2.86 2.86" />
    <circle cx="20.59" cy="3.41" r="1.91" />
    <circle cx="3.41" cy="20.59" r="1.91" />
    <circle cx="20.11" cy="20.11" r="2.39" />
    <circle cx="3.89" cy="3.89" r="2.39" />
    <path d="M7.95 16.05l-3.2 3.2" />
    <path d="M19.25 4.75l-3.2 3.2" />
    <path d="M17.73 12a5.74 5.74 0 1 1-1.68-4 5.69 5.69 0 0 1 1.68 4Z" />
    <path d="M18.42 18.42l-2.37-2.37" />
    <path d="M7.95 7.95L5.58 5.58" />
  </svg>
);


export const TrashIcon = ({className}: {className: string}): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.134-2.036-2.134H8.036C6.91 2.75 6 3.704 6 4.884v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
);

export const EyeIcon = ({className}: {className: string}): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
);

export const SparklesIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.898 20.572L16.5 21.75l-.398-1.178a3.375 3.375 0 00-2.456-2.456L12.5 17.25l1.178-.398a3.375 3.375 0 002.456-2.456L16.5 13.5l.398 1.178a3.375 3.375 0 002.456 2.456l1.178.398-1.178.398a3.375 3.375 0 00-2.456 2.456z" />
    </svg>
);

export const GripVerticalIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5.25l.75 7.5-7.5.75" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5.25.75 6" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 5.25l-.75 7.5 7.5.75" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 5.25l7.5.75" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 15l.75 7.5-7.5.75" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 15l-8.25.75" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-.75 7.5 7.5.75" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l7.5.75" />
    </svg>
);

export const ArrowDownTrayIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
);

export const LockClosedIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 00-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
    </svg>
);

export const ArrowUturnLeftIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
    </svg>
);

export const ArrowTopRightOnSquareIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
    </svg>
);

export const DocumentTextIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
);

export const LightBulbIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-1.83m-1.5 1.83a6.01 6.01 0 01-1.5-1.83m1.5 1.83v-5.25A2.25 2.25 0 0113.5 9.75h.511c.42 0 .822.166 1.121.445l.668.56a2.25 2.25 0 002.933-.53l.533-.667a2.25 2.25 0 012.831-.575l.533.226a2.25 2.25 0 011.423 2.184v.533c0 .42-.166.822-.445 1.121l-.56.668a2.25 2.25 0 00.53 2.933l.667.533a2.25 2.25 0 01.575 2.831l-.226.533a2.25 2.25 0 01-2.184 1.423h-.533a2.25 2.25 0 01-1.121-.445l-.668-.56a2.25 2.25 0 00-2.933.53l-.533.667a2.25 2.25 0 01-2.831.575l-.533-.226a2.25 2.25 0 01-1.423-2.184v-.533a2.25 2.25 0 01.445-1.121l.56-.668a2.25 2.25 0 00-.53-2.933l-.667-.533a2.25 2.25 0 01-.575-2.831l.226-.533a2.25 2.25 0 012.184-1.423h.533A2.25 2.25 0 0112 7.5v-2.25" />
    </svg>
);

export const XCircleIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

export const DashboardIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
    </svg>
);

export const ApplicationsIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
);

export const AtomGearIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 32 32"
    fill="currentColor"
    className={className}
    aria-hidden="true"
  >
    <path d="m30.323 20.301.598-3.625-1.316-.217a13.282 13.282 0 0 0-.337-3.435l1.24-.467-1.294-3.439-1.261.475a13.501 13.501 0 0 0-2.028-2.769l.885-1.078-2.84-2.331-.918 1.119a13.287 13.287 0 0 0-3.116-1.341l.248-1.502-3.625-.598-.261 1.579a13.281 13.281 0 0 0-3.28.393l-.589-1.564L8.99 2.795l.617 1.64a13.434 13.434 0 0 0-2.589 1.927l-1.401-1.15-2.331 2.84 1.442 1.184c-.533.9-.965 1.873-1.279 2.906l-1.876-.31-.598 3.625 1.895.313a13.27 13.27 0 0 0 .308 3.149l-1.803.679 1.294 3.439 1.787-.672a13.474 13.474 0 0 0 1.827 2.605L5.1 26.412l2.84 2.331 1.145-1.396a13.268 13.268 0 0 0 2.912 1.381l-.283 1.715 3.625.598.27-1.639a13.258 13.258 0 0 0 3.301-.252l.558 1.484 3.439-1.294-.532-1.413a13.483 13.483 0 0 0 2.786-1.922l1.119.918 2.331-2.84-1.072-.88a13.273 13.273 0 0 0 1.45-3.121l1.335.22zM17.896 5.936c-5.558-.917-10.808 2.845-11.725 8.403s2.845 10.808 8.403 11.725 10.808-2.845 11.725-8.403-2.845-10.808-8.403-11.725zm3.246 11.784-3.081-2.528-6.511 7.934-1.618-1.328 6.511-7.934-4.137-3.395 5.934-2.072 6.305 5.174-3.404 4.148z"/>
  </svg>
);

export const CheckBadgeIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

export const ClockIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

export const StrategyIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60" className={className} fill="currentColor">
    <path fillRule="evenodd" d="M31.293 42.707a.997.997 0 0 0 1.414 0L35 40.414l2.293 2.293a.997.997 0 0 0 1.414 0 .999.999 0 0 0 0-1.414L36.414 39l2.293-2.293a.999.999 0 1 0-1.414-1.414L35 37.586l-2.293-2.293a.999.999 0 1 0-1.414 1.414L33.586 39l-2.293 2.293a.999.999 0 0 0 0 1.414m22.414-.414a.999.999 0 0 0-1.414 0L50 44.586l-2.293-2.293a.999.999 0 1 0-1.414 1.414L48.586 46l-2.293 2.293a.999.999 0 1 0 1.414 1.414L50 47.414l2.293 2.293a.997.997 0 0 0 1.414 0 .999.999 0 0 0 0-1.414L51.414 46l2.293-2.293a.999.999 0 0 0 0-1.414M10.293 21.707a.997.997 0 0 0 1.414 0L14 19.414l2.293 2.293a.997.997 0 0 0 1.414 0 .999.999 0 0 0 0-1.414L15.414 18l2.293-2.293a.999.999 0 1 0-1.414-1.414L14 16.586l-2.293-2.293a.999.999 0 1 0-1.414 1.414L12.586 18l-2.293 2.293a.999.999 0 0 0 0 1.414m13.414 24.586a.999.999 0 0 0-1.414 0L20 48.586l-2.293-2.293a.999.999 0 1 0-1.414 1.414L18.586 50l-2.293 2.293a.999.999 0 1 0 1.414 1.414L20 51.414l2.293 2.293a.997.997 0 0 0 1.414 0 .999.999 0 0 0 0-1.414L21.414 50l2.293-2.293a.999.999 0 0 0 0-1.414M43 14c1.654 0 3-1.346 3-3s-1.346-3-3-3-3 1.346-3 3 1.346 3 3 3m0 2c-2.757 0-5-2.243-5-5s2.243-5 5-5 5 2.243 5 5-2.243 5-5 5M60 4v52c0 2.206-1.794 4-4 4H11a1 1 0 0 1-1-1V35c0-4.963 4.038-9 9-9s9 4.037 9 9v6c0 3.859 3.14 7 7 7s7-3.141 7-7V21.414l-4.293 4.293a.999.999 0 1 1-1.414-1.414l6-5.999a1.001 1.001 0 0 1 1.415 0l5.999 5.999a.999.999 0 1 1-1.414 1.414L44 21.414V41c0 4.963-4.038 9-9 9s-9-4.037-9-9v-6c0-3.859-3.14-7-7-7s-7 3.141-7 7v23h44c1.103 0 2-.897 2-2V4c0-1.103-.897-2-2-2H4c-1.103 0-2 .897-2 2v52c0 1.103.897 2 2 2h3a1 1 0 1 1 0 2H4c-2.206 0-4-1.794-4-4V4c0-2.206 1.794-4 4-4h52c2.206 0 4 1.794 4 4" />
  </svg>
);

export const RocketLaunchIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    className={className}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M2.77409 12.4814C3.07033 12.778 3.07004 13.2586 2.77343 13.5548L2.61779 13.7103C2.48483 13.8431 2.48483 14.058 2.61779 14.1908C2.75125 14.3241 2.96801 14.3241 3.10147 14.1908L4.8136 12.4807C5.1102 12.1845 5.59079 12.1848 5.88704 12.4814C6.18328 12.778 6.18298 13.2586 5.88638 13.5548L4.17426 15.2648C3.4481 15.9901 2.27116 15.9901 1.545 15.2648C0.818334 14.5391 0.818333 13.362 1.545 12.6362L1.70065 12.4807C1.99725 12.1845 2.47784 12.1848 2.77409 12.4814Z" />
    <path d="M7.68665 13.4896C7.98307 13.7861 7.98307 14.2667 7.68665 14.5631L5.54424 16.7055C5.24782 17.0019 4.76723 17.0019 4.4708 16.7055C4.17438 16.409 4.17438 15.9285 4.4708 15.632L6.61321 13.4896C6.90963 13.1932 7.39023 13.1932 7.68665 13.4896Z" />
    <path d="M10.4958 16.2953C10.7922 16.5918 10.7922 17.0724 10.4958 17.3688L8.36805 19.4965C8.07162 19.7929 7.59103 19.7929 7.29461 19.4965C6.99818 19.2001 6.99818 18.7195 7.29461 18.4231L9.42237 16.2953C9.71879 15.9989 10.1994 15.9989 10.4958 16.2953Z" />
    <path d="M7.29719 16.696C7.5903 16.9957 7.58495 17.4762 7.28525 17.7693L5.55508 19.4614C5.25538 19.7545 4.77481 19.7491 4.48171 19.4494C4.1886 19.1497 4.19395 18.6692 4.49365 18.3761L6.22382 16.684C6.52352 16.3909 7.00409 16.3963 7.29719 16.696Z" />
    <path d="M11.4811 18.118C11.7774 18.4146 11.7771 18.8952 11.4805 19.1915L9.76834 20.9015C9.63539 21.0343 9.63539 21.2492 9.76834 21.382C9.9018 21.5153 10.1186 21.5153 10.252 21.382L10.4077 21.2265C10.7043 20.9303 11.1849 20.9306 11.4811 21.2272C11.7774 21.5238 11.7771 22.0044 11.4805 22.3006L11.3248 22.4561C10.5987 23.1813 9.42171 23.1813 8.69556 22.4561C7.96889 21.7303 7.96889 20.5532 8.69556 19.8274L10.4077 18.1174C10.7043 17.8211 11.1849 17.8214 11.4811 18.118Z" />
    <path d="M10.8463 5.40912L8.65863 7.59023C8.2565 7.99113 7.88763 8.35888 7.59632 8.69132C7.40925 8.90481 7.2223 9.13847 7.06394 9.39666C6.58134 8.92621 6.13406 8.63287 5.64368 8.43084C4.77069 8.08451 4.65309 7.51645 4.98886 7.1817C5.9525 6.22099 7.10949 5.06751 7.66786 4.83584C8.1603 4.63152 8.69225 4.56354 9.20531 4.63936C9.67539 4.70883 10.1201 4.9503 10.8463 5.40912Z" />
    <path d="M14.5818 16.8932C14.7581 17.0722 14.8752 17.1985 14.981 17.3336C15.1207 17.5118 15.2456 17.7011 15.3544 17.8995C15.4769 18.1229 15.5721 18.3615 15.7623 18.8388C15.9172 19.2273 16.4317 19.33 16.7306 19.032L16.8029 18.9599C17.7665 17.9992 18.9235 16.8457 19.1558 16.289C19.3608 15.7981 19.429 15.2677 19.3529 14.7562C19.2832 14.2876 19.0411 13.8443 18.581 13.1204L16.386 15.3088C15.9748 15.7188 15.5977 16.0948 15.2567 16.3893C15.0523 16.5658 14.8287 16.7422 14.5818 16.8932Z" />
    <path d="M15.5023 14.3674L20.5319 9.35289C21.2563 8.63072 21.6185 8.26963 21.8092 7.81046C22 7.3513 22 6.84065 22 5.81937V5.33146C22 3.76099 22 2.97576 21.5106 2.48788C21.0213 2 20.2337 2 18.6585 2H18.1691C17.1447 2 16.6325 2 16.172 2.19019C15.7114 2.38039 15.3493 2.74147 14.6249 3.46364L9.59522 8.47817C8.74882 9.32202 8.224 9.84526 8.02078 10.3506C7.95657 10.5103 7.92446 10.6682 7.92446 10.8339C7.92446 11.5238 8.48138 12.0791 9.59522 13.1896L9.74492 13.3388L11.4985 11.5591C11.7486 11.3053 12.1571 11.3022 12.4109 11.5523C12.6647 11.8024 12.6678 12.2109 12.4177 12.4647L10.6587 14.2499L10.7766 14.3674C11.8905 15.4779 12.4474 16.0331 13.1394 16.0331C13.2924 16.0331 13.4387 16.006 13.5858 15.9518C14.1048 15.7607 14.6345 15.2325 15.5023 14.3674ZM17.8652 8.47854C17.2127 9.12904 16.1548 9.12904 15.5024 8.47854C14.8499 7.82803 14.8499 6.77335 15.5024 6.12284C16.1548 5.47233 17.2127 5.47233 17.8652 6.12284C18.5177 6.77335 18.5177 7.82803 17.8652 8.47854Z" />
  </svg>
);

export const MagnifyingGlassPlusIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6" />
    </svg>
);

export const NetworkingIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    xmlSpace="preserve"
    viewBox="0 0 2.333 2.333"
    fill="currentColor"
    className={className}
    aria-hidden="true"
  >
    <g id="SVGRepo_iconCarrier">
      <defs>
        <style>{'.fil0{fill:#000}'}</style>
      </defs>
      <g id="Layer_x0020_1">
        <path
          className="fil0"
          d="M.583.85A.084.084 0 0 1 .499.765a.084.084 0 0 1 .167 0 .083.083 0 0 1-.083.083zm0-.128a.045.045 0 0 0-.045.044C.538.79.56.81.583.81.606.81.627.79.627.766A.044.044 0 0 0 .583.722zM.824.85A.084.084 0 0 1 .741.765c0-.047.038-.083.083-.083.048 0 .084.037.084.083a.084.084 0 0 1-.084.083zm0-.128c-.06 0-.057.088 0 .088s.057-.088 0-.088zM1.065.85A.084.084 0 0 1 .98.765a.084.084 0 0 1 .167 0 .084.084 0 0 1-.083.083zm0-.128a.045.045 0 0 0-.045.044c0 .024.021.044.045.044.023 0 .044-.02.044-.044a.046.046 0 0 0-.044-.044z"
        />
        <path
          className="fil0"
          d="M.352 1.242a.02.02 0 0 1-.018-.03l.103-.182A.364.364 0 0 1 .313.765c0-.224.23-.406.511-.406.28 0 .51.182.51.406 0 .223-.23.407-.51.407a.603.603 0 0 1-.22-.04l-.243.109-.009.001zm.127-.205-.08.143.195-.086a.024.024 0 0 1 .023.001.565.565 0 0 0 .207.038c.26 0 .47-.164.47-.366 0-.2-.211-.368-.47-.368-.26 0-.47.164-.47.366 0 .09.041.175.119.243.011.007.012.02.006.029z"
        />
        <path
          className="fil0"
          d="M1.75 1.58a.084.084 0 0 1-.084-.084c0-.045.037-.083.083-.083.046 0 .084.038.084.083a.083.083 0 0 1-.084.084zm0-.128a.046.046 0 0 0-.045.044c0 .024.02.045.044.045.024 0 .045-.02.045-.045a.045.045 0 0 0-.045-.044zM1.509 1.58a.084.084 0 0 1-.083-.084c0-.045.037-.083.083-.083.046 0 .083.038.083.083a.084.084 0 0 1-.083.084zm0-.128a.046.046 0 0 0-.044.044c0 .024.02.045.044.045.024 0 .044-.02.044-.045a.046.046 0 0 0-.044-.044zM1.269 1.58a.084.084 0 0 1-.084-.084.084.084 0 0 1 .167 0 .084.084 0 0 1-.083.084zm0-.128c-.058 0-.06.089 0 .089.056 0 .056-.089 0-.089z"
        />
        <path
          className="fil0"
          d="m1.981 1.974-.008-.001-.245-.11a.614.614 0 0 1-.219.039c-.28 0-.51-.182-.51-.406 0-.223.23-.405.51-.405.282 0 .511.182.511.405a.359.359 0 0 1-.125.266l.103.183c.006.01 0 .03-.017.03zm-.253-.153c.005 0 .007.002.011.003l.195.088-.08-.143a.021.021 0 0 1 .004-.028c.279-.249.04-.608-.35-.608-.26 0-.47.164-.47.365 0 .201.211.365.47.365.132 0 .208-.042.22-.042z"
        />
      </g>
    </g>
  </svg>
);

export const MicrophoneIcon = ({ className }: { className: string }): React.ReactNode => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className={className}>
    <g fill="currentColor">
      <path d="M12 2a5.75 5.75 0 0 0-5.75 5.75v3a5.75 5.75 0 0 0 11.451.75H13a.75.75 0 0 1 0-1.5h4.75V8.5H13A.75.75 0 0 1 13 7h4.701A5.751 5.751 0 0 0 12 2Z"/>
      <path fillRule="evenodd" clipRule="evenodd" d="M4 9a.75.75 0 0 1 .75.75v1a7.25 7.25 0 1 0 14.5 0v-1a.75.75 0 0 1 1.5 0v1a8.75 8.75 0 0 1-8 8.718v2.282a.75.75 0 0 1-1.5 0v-2.282a8.75 8.75 0 0 1-8-8.718v-1A.75.75 0 0 1 4 9Z"/>
    </g>
  </svg>
);

export const ResumeIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m9.375 10.5a9.06 9.06 0 003.01-5.617c.01-.03.01-.06.01-.09v-3.375c0-.621-.504-1.125-1.125-1.125H15Z" />
    </svg>
);

export const CompanyIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h6M9 11.25h6m-6 4.5h6M6.75 21v-2.25a2.25 2.25 0 012.25-2.25h6a2.25 2.25 0 012.25 2.25V21" />
    </svg>
);

export const LinkedInIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={className}>
        <path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 118.25 6.5 1.75 1.75 0 016.5 8.25zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.4 1.4 0 0013 13.19V19h-3v-9h2.9v1.3a3.11 3.11 0 012.7-1.4c1.55 0 3.36.96 3.36 4.66z" />
    </svg>
);

export const ArrowTrendingUpIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-3.75-2.25m3.75 2.25V4.5" />
    </svg>
);

export const CurrencyDollarIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182.79-.623 1.72-1 2.65-1 .59 0 1.17.15 1.68.423" />
    </svg>
);

export const ClipboardDocumentListIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
    </svg>
);

export const ClipboardDocumentCheckIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.125 2.25h-4.5c-1.125 0-2.062.938-2.062 2.063v15.375c0 1.125.938 2.063 2.063 2.063h12.75c1.125 0 2.063-.938 2.063-2.063V12.063" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 1.5l4.5 4.5m-4.5-4.5v4.5h4.5m-1.625 7.875-3.182-3.182a.75.75 0 00-1.06 0l-1.06 1.06a.75.75 0 000 1.06l3.182 3.182a.75.75 0 001.06 0l4.5-4.5a.75.75 0 000-1.06l-1.06-1.06a.75.75 0 00-1.06 0l-3.182 3.182Z" />
    </svg>
);

export const CircleStackIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375" />
    </svg>
);

export const ChevronLeftIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
    </svg>
);

export const ChevronRightIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
    </svg>
);

export const ThumbUpIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75A2.25 2.25 0 0116.5 4.5c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H14.25c-.193 0-.383.062-.562.18a.75.75 0 01-.79 0c-.179-.118-.369-.18-.562-.18H10.5a2.25 2.25 0 01-1.497-4.05c.29-.502.83-1.314.83-1.314-.194.002-.39-.025-.583-.08a4.067 4.067 0 01-2.068-1.486c-.33-.467-.513-1.025-.569-1.581a.75.75 0 01.068-.8A.75.75 0 013 6.25H4.23a2.25 2.25 0 012.11 1.566c.08.204.142.413.182.628a.75.75 0 01-.158.74c-.178.22-.44.42-.715.59A2.25 2.25 0 016.632 10.5z" />
    </svg>
);

export const ThumbDownIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 15h2.25m8.024-9.75c-.011 1.218-.097 2.596-.683 3.847-.312.605-.945.948-1.627.907h-3.126c-.663 0-.948-.477-.725-1.282.266-.558.362-.914.723-1.218A2.25 2.25 0 0016.5 6v-.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v15.15c0 1.411.704 2.671 1.773 3.33a1.464 1.464 0 001.738 0 1.593 1.593 0 000-2.252c-.624-.667-.756-1.472-.378-2.192.345-.691.803-1.408 1.27-2.042a5.317 5.317 0 011.374-1.664c.422-.312.652-.577.655-.979.006-.61.168-1.076.57-1.519.176-.186.336-.429.429-.64a.619.619 0 00.008-.666 1.554 1.554 0 01-.122-.231c-.055-.139-.055-.277 0-.415a.618.618 0 00-.062-.406c-.081-.13-.22-.512-.417-.833a2.197 2.197 0 00-.833-.694c-.37-.22-.786-.33-1.22-.383-.264-.03-.349.26-.336.52.046.038.129.068.25.112a3.498 3.498 0 01.655.316c.295.186.375.612.185.914-.092.141-.214.241-.363.218-.29-.052-.566.009-.866.25-.502.353-.955.652-1.417.93a1.415 1.415 0 00-.47.433c-.121.247-.11.544-.11.79v.1c0 1.238.37 2.42 1.054 3.45.345.522.76.98 1.23 1.4-.78.243-1.744.378-2.74.378H3.75a2.25 2.25 0 01-2.25-2.25v-2.25z" />
    </svg>
);

export const InformationCircleIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
    </svg>
);

export const TableCellsIcon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
    </svg>
);

export const Squares2X2Icon = ({ className }: { className: string }): React.ReactNode => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
    </svg>
);

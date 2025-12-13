import React from 'react';
import type { WidgetProps } from '../../../../types';
import type { StrategicOpeningData } from '../../../../types';
import { formatTimestamp } from '../utils';

export const StrategicOpeningWidget = ({
    data,
    onChange,
    editable,
    mode,
    lastUpdated,
}: WidgetProps<StrategicOpeningData>) => {
    if (!editable || mode === 'live') {
        return (
            <div className="space-y-2">
                <p className="text-sm italic text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{data.opening}</p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
            </div>
        );
    }

    return (
        <div className="space-y-2">
            <textarea
                value={data.opening}
                onChange={(event) => onChange({ ...data, opening: event.target.value })}
                rows={6}
                className="w-full rounded-md border border-slate-300 bg-white p-3 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Last updated: {formatTimestamp(lastUpdated)}</p>
        </div>
    );
};

export default StrategicOpeningWidget;

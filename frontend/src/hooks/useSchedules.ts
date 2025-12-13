import { useState, useEffect, useCallback } from 'react';
import * as apiService from '../services/apiService';
import { SiteSchedule, SiteSchedulePayload, SiteDetails } from '../types';
import { useToast } from './useToast';

interface ScheduleState {
    schedules: SiteSchedule[];
    sites: SiteDetails[];
    isLoading: boolean;
    error: string | null;
}

// Main hook for schedule management
export const useScheduleManager = () => {
    const [state, setState] = useState<ScheduleState>({
        schedules: [],
        sites: [],
        isLoading: true,
        error: null,
    });
    const { addToast } = useToast();

    // Fetch data function
    const fetchData = useCallback(async () => {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        try {
            const [schedulesData, sitesData] = await Promise.all([
                apiService.getSiteSchedules(),
                apiService.getJobSites(),
            ]);
            setState({
                schedules: schedulesData,
                sites: sitesData,
                isLoading: false,
                error: null,
            });
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data';
            setState(prev => ({
                ...prev,
                isLoading: false,
                error: errorMessage,
            }));
        }
    }, []);

    // Create schedule
    const createSchedule = useCallback(async (payload: SiteSchedulePayload) => {
        try {
            await apiService.createSiteSchedule(payload);
            addToast('Schedule created successfully!', 'success');
            await fetchData(); // Refresh data
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to create schedule';
            addToast(errorMessage, 'error');
            throw err;
        }
    }, [addToast, fetchData]);

    // Update schedule
    const updateSchedule = useCallback(async (scheduleId: string, payload: SiteSchedulePayload) => {
        try {
            await apiService.updateSiteSchedule(scheduleId, payload);
            addToast('Schedule updated successfully!', 'success');
            await fetchData(); // Refresh data
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to update schedule';
            addToast(errorMessage, 'error');
            throw err;
        }
    }, [addToast, fetchData]);

    // Delete schedule
    const deleteSchedule = useCallback(async (scheduleId: string) => {
        try {
            await apiService.deleteSiteSchedule(scheduleId);
            addToast('Schedule deleted successfully!', 'success');
            await fetchData(); // Refresh data
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to delete schedule';
            addToast(errorMessage, 'error');
            throw err;
        }
    }, [addToast, fetchData]);

    // Toggle schedule enabled/disabled
    const toggleSchedule = useCallback(async (schedule: SiteSchedule) => {
        try {
            await apiService.updateSiteSchedule(schedule.id, { enabled: !schedule.enabled });
            addToast(`Schedule ${!schedule.enabled ? 'enabled' : 'disabled'}!`, 'success');
            await fetchData(); // Refresh data
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to toggle schedule';
            addToast(errorMessage, 'error');
            throw err;
        }
    }, [addToast, fetchData]);

    // Initial data fetch
    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return {
        ...state,
        refetch: fetchData,
        createSchedule,
        updateSchedule,
        deleteSchedule,
        toggleSchedule,
    };
};

// Helper function to check for schedule conflicts
export const checkScheduleConflicts = (schedules: SiteSchedule[], siteName: string, intervalMinutes: number, excludeId?: string) => {
    const siteSchedules = schedules.filter(s => s.site_name === siteName && s.id !== excludeId && s.enabled);
    
    // Check for timing conflicts (schedules that might overlap)
    const potentialConflicts = siteSchedules.filter(s => {
        const timeDifference = Math.abs(s.interval_minutes - intervalMinutes);
        return timeDifference < 30; // Less than 30 minutes difference might cause conflicts
    });
    
    return {
        hasConflicts: potentialConflicts.length > 0,
        conflicts: potentialConflicts,
        totalSchedulesForSite: siteSchedules.length,
        recommendedInterval: Math.max(60, ...siteSchedules.map(s => s.interval_minutes)) + 30, // Suggest 30 mins buffer
    };
};

// Helper function to get schedule requirements and validation info
export const getScheduleRequirements = (sites: SiteDetails[], siteName: string) => {
    const siteDetails = sites.find(s => s.site_name === siteName);
    
    return {
        siteDetails,
        requirements: {
            minInterval: 30, // Minimum 30 minutes between scrapes
            maxInterval: 1440, // Maximum 24 hours
            requiredFields: ['site_name', 'interval_minutes', 'enabled'],
            optionalFields: ['payload'],
        },
        recommendations: [
            'Set intervals of at least 60 minutes to avoid rate limiting',
            'Use different intervals for multiple schedules on the same site',
            'Consider peak usage times when scheduling scrapes',
            'Enable schedules only when needed to reduce server load',
        ],
    };
};
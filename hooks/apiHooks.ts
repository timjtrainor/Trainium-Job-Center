import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as apiService from '../services/apiService';
import {
  Company,
  BaseResume,
  Resume,
  SiteSchedule,
  SiteDetails,
  SiteSchedulePayload,
  TaskRunRecord,
  TaskEnqueueResponse,
  ResumeTailoringJobPayload,
  CompanyResearchJobPayload,
} from '../types';

export const useGetCompanies = () => {
  return useQuery<Company[], Error>({
    queryKey: ['companies'],
    queryFn: apiService.getCompanies,
  });
};

export const useGetBaseResumes = () => {
  return useQuery<BaseResume[], Error>({
    queryKey: ['baseResumes'],
    queryFn: apiService.getBaseResumes,
  });
};

export const useGetResumeContent = (resumeId: string, enabled = true) => {
  return useQuery<Resume, Error>({
    queryKey: ['resumeContent', resumeId],
    queryFn: () => apiService.getResumeContent(resumeId),
    enabled,
  });
};

export const useCheckPostgrestHealth = () => {
  return useMutation(apiService.checkPostgrestHealth);
};

export const useCheckFastApiHealth = () => {
  return useMutation(apiService.checkFastApiHealth);
};

export const useGetSiteSchedules = () => {
  return useQuery<SiteSchedule[], Error>({
    queryKey: ['siteSchedules'],
    queryFn: apiService.getSiteSchedules,
  });
};

export const useGetJobSites = () => {
  return useQuery<SiteDetails[], Error>({
    queryKey: ['jobSites'],
    queryFn: apiService.getJobSites,
  });
};

export const useCreateSiteSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiService.createSiteSchedule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['siteSchedules'] }),
  });
};

export const useUpdateSiteSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ scheduleId, payload }: { scheduleId: string; payload: SiteSchedulePayload }) =>
      apiService.updateSiteSchedule(scheduleId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['siteSchedules'] }),
  });
};

export const useDeleteSiteSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scheduleId: string) => apiService.deleteSiteSchedule(scheduleId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['siteSchedules'] }),
  });
};

export const useEnqueueResumeTailoringJob = () => {
  return useMutation<TaskEnqueueResponse, Error, ResumeTailoringJobPayload>({
    mutationFn: apiService.enqueueResumeTailoringJob,
  });
};

export const useEnqueueCompanyResearchJob = () => {
  return useMutation<TaskEnqueueResponse, Error, CompanyResearchJobPayload>({
    mutationFn: apiService.enqueueCompanyResearchJob,
  });
};

interface TaskRunStatusOptions {
  enabled?: boolean;
  refetchInterval?: number;
}

export const useTaskRunStatus = (
  runId: string | null,
  { enabled = true, refetchInterval = 4000 }: TaskRunStatusOptions = {}
) => {
  return useQuery<TaskRunRecord, Error>({
    queryKey: ['taskRunStatus', runId],
    queryFn: () => apiService.getTaskRunStatus(runId!),
    enabled: Boolean(runId) && enabled,
    refetchInterval: (data) => {
      if (!runId || !enabled) return false;
      if (!data) return refetchInterval;
      return data.status === 'succeeded' || data.status === 'failed' ? false : refetchInterval;
    },
  });
};


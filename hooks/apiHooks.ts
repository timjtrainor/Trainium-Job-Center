import { useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as apiService from '../services/apiService';
import { Company, BaseResume, Resume, SiteSchedule, SiteDetails, SiteSchedulePayload } from '../types';
import { ReviewedJobsFilters, ReviewedJobsSort, JobReviewOverrideRequest } from '../services/apiService';

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

type ReviewedJobsQueryArgs = {
  page?: number;
  size?: number;
  filters?: ReviewedJobsFilters;
  sort?: ReviewedJobsSort;
};

export const useReviewedJobs = ({ page = 1, size = 15, filters = {}, sort = { by: 'date_posted', order: 'desc' } }: ReviewedJobsQueryArgs) => {
  const navigate = useNavigate();
  const location = useLocation();

  const apiSearchString = useMemo(
    () => apiService.buildReviewedJobsSearchParams({ page, size, filters, sort }).toString(),
    [page, size, filters, sort]
  );

  const uiSearchString = useMemo(
    () => apiService.buildReviewedJobsUiSearchParams({ page, size, filters, sort }).toString(),
    [page, size, filters, sort]
  );

  useEffect(() => {
    const nextSearch = uiSearchString ? `?${uiSearchString}` : '';
    if (location.search !== nextSearch) {
      navigate(`${location.pathname}${nextSearch}`, { replace: true });
    }
  }, [uiSearchString, location.pathname, location.search, navigate]);

  return useQuery({
    queryKey: ['reviewedJobs', apiSearchString],
    queryFn: () => apiService.getReviewedJobs({ page, size, filters, sort }),
    keepPreviousData: true,
  });
};

export const useOverrideJobReview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, payload }: { jobId: string; payload: JobReviewOverrideRequest }) =>
      apiService.overrideJobReview(jobId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewedJobs'] });
    },
  });
};


import api from './client';
import type { AnalyticsOverview, ClassStats, StoreyStats, IssuesSummary, Completeness } from '../types';

export const getOverview = (projectId: string) =>
  api.get<AnalyticsOverview>(`/models/${projectId}/analytics/overview`);

export const getByClass = (projectId: string) =>
  api.get<ClassStats[]>(`/models/${projectId}/analytics/by-class`);

export const getByStorey = (projectId: string) =>
  api.get<StoreyStats[]>(`/models/${projectId}/analytics/by-storey`);

export const getIssuesSummary = (projectId: string) =>
  api.get<IssuesSummary>(`/models/${projectId}/analytics/issues-summary`);

export const getCompleteness = (projectId: string) =>
  api.get<Completeness>(`/models/${projectId}/analytics/completeness`);

import api from './client';
import type { Issue, IssueCreate, IssueUpdate, Paginated } from '../types';

interface IssueFilters {
  status?: string;
  severity?: string;
  category?: string;
  issue_type?: string;
  page?: number;
  page_size?: number;
}

export const getIssues = (projectId: string, filters: IssueFilters = {}) =>
  api.get<Paginated<Issue>>(`/models/${projectId}/issues`, { params: filters });

export const createIssue = (projectId: string, data: IssueCreate) =>
  api.post<Issue>(`/models/${projectId}/issues`, data);

export const getIssue = (projectId: string, issueId: string) =>
  api.get<Issue>(`/models/${projectId}/issues/${issueId}`);

export const updateIssue = (projectId: string, issueId: string, data: IssueUpdate) =>
  api.put<Issue>(`/models/${projectId}/issues/${issueId}`, data);

export const deleteIssue = (projectId: string, issueId: string) =>
  api.delete(`/models/${projectId}/issues/${issueId}`);

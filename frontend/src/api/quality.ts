import api from './client';
import type { QCRule, QCRuleCreate, QCRunResult } from '../types';

export const runQC = (projectId: string) =>
  api.post<QCRunResult>(`/models/${projectId}/qc/run`);

export const getQCResults = (projectId: string) =>
  api.get(`/models/${projectId}/qc/results`);

export const getRules = () => api.get<QCRule[]>('/qc-rules');

export const createRule = (data: QCRuleCreate) => api.post<QCRule>('/qc-rules', data);

export const updateRule = (id: string, data: Partial<QCRuleCreate>) =>
  api.put<QCRule>(`/qc-rules/${id}`, data);

export const deleteRule = (id: string) => api.delete(`/qc-rules/${id}`);

import api from './client';
import type { Project, ProjectDetail } from '../types';

export const getProjects = () => api.get<Project[]>('/projects');

export const getProject = (id: string) => api.get<ProjectDetail>(`/projects/${id}`);

export const deleteProject = (id: string) => api.delete(`/projects/${id}`);

export const uploadModel = (file: File, name: string, description?: string) => {
  const form = new FormData();
  form.append('file', file);
  form.append('name', name);
  if (description) form.append('description', description);
  return api.post<Project>('/models/upload', form);
};

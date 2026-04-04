import api from './client';
import type { Building, Storey, Space, TreeData } from '../types';

export const getTree = (projectId: string) =>
  api.get<TreeData>(`/models/${projectId}/tree`);

export const getBuildings = (projectId: string) =>
  api.get<Building[]>(`/models/${projectId}/buildings`);

export const getStoreys = (projectId: string) =>
  api.get<Storey[]>(`/models/${projectId}/storeys`);

export const getSpaces = (projectId: string) =>
  api.get<Space[]>(`/models/${projectId}/spaces`);

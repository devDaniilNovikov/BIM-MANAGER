import api from './client';
import type { Element, ElementDetail, Paginated } from '../types';

interface ElementFilters {
  ifc_class?: string;
  storey_name?: string;
  search?: string;
  has_issues?: boolean;
  page?: number;
  page_size?: number;
}

export const getElements = (projectId: string, filters: ElementFilters = {}) =>
  api.get<Paginated<Element>>(`/models/${projectId}/elements`, { params: filters });

export const getElement = (projectId: string, elementId: string) =>
  api.get<ElementDetail>(`/models/${projectId}/elements/${elementId}`);

export const getElementProperties = (projectId: string, elementId: string) =>
  api.get(`/models/${projectId}/elements/${elementId}/properties`);

export const getElementClasses = (projectId: string) =>
  api.get<{ ifc_class: string; count: number }[]>(`/models/${projectId}/element-classes`);

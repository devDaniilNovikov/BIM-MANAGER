export interface Project {
  id: string;
  name: string;
  description: string | null;
  file_name: string;
  file_size: number;
  ifc_schema: string | null;
  created_at: string;
  element_count: number | null;
  issue_count: number | null;
}

export interface Building {
  id: string;
  global_id: string;
  name: string | null;
  storeys: Storey[];
}

export interface Storey {
  id: string;
  global_id: string;
  name: string | null;
  elevation: number | null;
  spaces: Space[];
}

export interface Space {
  id: string;
  global_id: string;
  name: string | null;
  long_name: string | null;
  area: number | null;
  volume: number | null;
}

export interface ProjectDetail extends Project {
  buildings: Building[];
}

export interface Element {
  id: string;
  global_id: string;
  ifc_class: string;
  name: string | null;
  type_name: string | null;
  description: string | null;
  material: string | null;
  storey_name: string | null;
  space_name: string | null;
  length: number | null;
  width: number | null;
  height: number | null;
  area: number | null;
  volume: number | null;
  weight: number | null;
  is_problematic: boolean;
}

export interface ElementDetail extends Element {
  properties_json: string | null;
  has_name: boolean | null;
  has_type: boolean | null;
  has_storey: boolean | null;
  has_material: boolean | null;
  has_quantities: boolean | null;
  issues: Issue[];
}

export interface Issue {
  id: string;
  element_id: string | null;
  issue_type: string;
  severity: string;
  category: string;
  title: string | null;
  message: string;
  recommendation: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface IssueCreate {
  element_id?: string;
  issue_type?: string;
  severity?: string;
  category: string;
  title?: string;
  message: string;
}

export interface IssueUpdate {
  status?: string;
  message?: string;
  title?: string;
  severity?: string;
}

export interface QCRule {
  id: string;
  name: string;
  description: string | null;
  ifc_class: string;
  check_type: string;
  check_config: string | null;
  severity: string;
  is_active: boolean;
}

export interface QCRuleCreate {
  name: string;
  description?: string;
  ifc_class?: string;
  check_type: string;
  check_config?: string;
  severity?: string;
  is_active?: boolean;
}

export interface Paginated<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface AnalyticsOverview {
  total_elements: number;
  total_buildings: number;
  total_storeys: number;
  total_spaces: number;
  total_issues: number;
  total_area: number;
  total_volume: number;
}

export interface ClassStats {
  ifc_class: string;
  count: number;
  total_area: number;
  total_volume: number;
}

export interface StoreyStats {
  storey_name: string;
  element_count: number;
  problematic_count: number;
}

export interface IssuesSummary {
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
}

export interface Completeness {
  total: number;
  with_name: number;
  with_type: number;
  with_storey: number;
  with_material: number;
  with_quantities: number;
  pct_name: number;
  pct_type: number;
  pct_storey: number;
  pct_material: number;
  pct_quantities: number;
}

export interface QCRunResult {
  status: string;
  total_issues: number;
  errors: number;
  warnings: number;
  info: number;
}

export interface TreeData {
  project_id: string;
  project_name: string;
  buildings: Building[];
}

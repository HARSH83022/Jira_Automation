export interface Developer {
  id: number
  name: string
  is_active: boolean
  created_at?: string
}

export interface DeveloperStat {
  name: string
  assigned_sp: number
  completed_sp: number
  remaining_sp: number
  completion_pct: number
  morning_assigned?: number | null
  morning_completed?: number | null
  morning_pct?: number | null
  movement_pct?: number | null
}

export interface ReportDeveloperRow {
  name: string
  assigned_sp: number
  completed_sp: number
  remaining_sp: number
  completion_pct: number
}

export interface ReportResult {
  report_id: number
  sprint: string
  sprint_id?: string | null
  sprint_start?: string | null
  sprint_end?: string | null
  day1_fixed_scope?: number | null
  report_date: string
  file_name: string
  total_scope: number
  completed_sp: number
  remaining_sp: number
  completion_pct: number
  total_stories: number
  completed_stories: number
  open_stories: number
  stories_without_sp: number
  stories_without_dev: number
  has_morning: boolean
  morning_scope: number
  morning_completed: number
  morning_pct: number
  scope_change: number
  daily_movement: number
  developers: DeveloperStat[]
  warnings: string[]
}

export interface ReportDetailResponse extends ReportResult {
  developer_data?: ReportDeveloperRow[]
  file_path?: string
  snapshot_type?: string
  created_at?: string
}

export interface ReportHistory {
  id: number
  file_name: string
  sprint?: string
  sprint_id?: string | null
  sprint_start?: string | null
  sprint_end?: string | null
  day1_fixed_scope?: number | null
  report_date?: string
  snapshot_type: string
  total_scope: number
  completed_sp: number
  completion_percentage: number
  created_at: string
}

export interface ValidationResult {
  valid: boolean
  error?: string
  total_rows?: number
  total_stories?: number
  detected_columns?: string[]
  sprint?: string
  warnings?: string[]
  summary?: {
    total_scope: number
    completed_sp: number
    completion_pct: number
  }
}

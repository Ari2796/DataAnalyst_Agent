export type ChartType = 'bar' | 'line' | 'pie' | 'scatter' | 'area' | 'histogram';

export interface ChartSeries {
  key: string;
  name: string;
  color?: string;
}

export interface ChartSpec {
  chart_type: ChartType;
  title: string;
  description?: string;
  x_axis_key: string;
  x_axis_label?: string;
  y_axis_label?: string;
  series: ChartSeries[];
  data: Record<string, any>[];
}

export interface NumericStats {
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  std?: number;
  q25?: number;
  q75?: number;
}

export interface ColumnProfile {
  name: string;
  data_type: string;
  general_type: string;
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  sample_values: any[];
  suggested_role?: string;
  stats?: NumericStats;
}

export interface SemanticMapping {
  column_name: string;
  mapped_role: string;
  confidence: number;
  is_confirmed: boolean;
  notes?: string;
}

export interface DatasetProfile {
  dataset_id: string;
  filename: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  duplicate_rows: number;
  columns: ColumnProfile[];
  semantic_mappings: Record<string, SemanticMapping>;
  suggested_questions: string[];
  created_at: string;
}

export interface DatasetPreview {
  dataset_id: string;
  filename: string;
  total_rows: number;
  columns: string[];
  preview_rows: Record<string, any>[];
}

export interface ToolCallRecord {
  tool_name: string;
  arguments: Record<string, any>;
  result_summary: string;
  success: boolean;
}

export interface DataTable {
  title?: string;
  columns: string[];
  rows: Record<string, any>[];
  total_count: number;
}

export interface ChatResponse {
  dataset_id: string;
  message: string;
  data_table?: DataTable;
  chart_spec?: ChartSpec;
  tool_calls: ToolCallRecord[];
  follow_up_suggestions: string[];
  limitations?: string[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  dataTable?: DataTable;
  chartSpec?: ChartSpec;
  toolCalls?: ToolCallRecord[];
  followUps?: string[];
  limitations?: string[];
}

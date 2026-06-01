// All shared TypeScript interfaces — strict mode, no `any`

export interface QueryRequest {
  query: string;
  schema_name: string;
  stream?: boolean;
  session_id?: string;
}

export interface ResultData {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  row_count: number;
}

export interface ChartConfig {
  type: "bar" | "line" | "pie" | "scalar" | "table";
  x_key?: string;
  y_key?: string;
  y_keys?: string[];
  title?: string;
  layout?: "horizontal" | "vertical";
  value?: string | number | null;
  label?: string;
}

export interface AttemptRecord {
  attempt: number;
  sql: string;
  error?: string;
}

export interface QueryResponse {
  success: boolean;
  query_id: string;
  generated_sql?: string;
  explanation?: string;
  result?: ResultData;
  chart_config?: ChartConfig;
  attempt_count: number;
  execution_time_ms: number;
  cached: boolean;
  error?: string;
  attempts?: AttemptRecord[];
}

export interface HistoryItem {
  id: string;
  natural_language: string;
  generated_sql?: string;
  success: boolean;
  attempt_count: number;
  error_message?: string;
  execution_time_ms?: number;
  result_row_count?: number;
  schema_used?: string;
  created_at: string;
}

export interface HistoryListResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface ColumnInfo {
  name: string;
  original_name: string;
  dtype: string;
  sql_type: string;
  nullable: boolean;
}

export interface UploadResponse {
  success: boolean;
  schema_name: string;
  table_name: string;
  original_filename: string;
  row_count: number;
  column_count: number;
  columns: ColumnInfo[];
  message: string;
}

export interface TableColumn {
  name: string;
  type: string;
  nullable: boolean;
}

export interface TableInfo {
  columns: TableColumn[];
  foreign_keys: { column: string; referred_table: string; referred_column: string }[];
  row_count: number;
}

export interface SchemaInfo {
  schema: string;
  tables: Record<string, TableInfo>;
}

export interface StreamMessage {
  type: "step" | "result" | "error";
  step?: string;
  steps?: string[];
  data?: QueryResponse;
  error?: string;
}

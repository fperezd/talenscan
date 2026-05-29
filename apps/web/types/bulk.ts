export type BulkEvaluationItem = {
  file_name: string;
  status: "created" | "duplicate" | "error";
  candidate_id: number | null;
  candidate_name: string | null;
  evaluation_id: number | null;
  pipeline_item_id: number | null;
  error: string | null;
};

export type BulkEvaluationResponse = {
  items: BulkEvaluationItem[];
  total: number;
  created_count: number;
  duplicate_count: number;
  error_count: number;
};

export type BulkLinkedInItem = {
  url: string;
  status: "created" | "duplicate" | "error";
  candidate_id: number | null;
  candidate_name: string | null;
  pipeline_item_id: number | null;
  error: string | null;
};

export type BulkLinkedInResponse = {
  items: BulkLinkedInItem[];
  total: number;
  created_count: number;
  duplicate_count: number;
  error_count: number;
};

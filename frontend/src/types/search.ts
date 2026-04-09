export interface SearchResult {
  content: string
  file_id: string
  original_name: string
  page_number: number | null
  section_title: string | null
  importance_score: number
}

export interface SearchRequest {
  query: string
  top_k?: number
}

export interface SearchResponse {
  results: SearchResult[]
  query: string
  total: number
}

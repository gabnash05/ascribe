export type FileStatus = 'PROCESSING' | 'READY' | 'FAILED' | 'FAILED'
export type FileType = 'PDF' | 'IMAGE' | 'DOCX' | 'TXT' | 'NOTE'

export interface VaultFile {
  id: string
  vault_id: string
  user_id: string
  original_name: string
  file_type: FileType
  mime_type: string | null
  size_bytes: number | null
  page_count: number | null
  status: FileStatus
  error_message: string | null
  total_chunks: number
  total_tokens: number
  file_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface FileUploadResponse {
  file_id: string
  status: FileStatus
}

export interface FileStatusResponse {
  file_id: string
  status: FileStatus
  total_chunks: number
  error_message?: string | null
}

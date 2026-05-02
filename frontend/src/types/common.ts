import type { VaultFile } from './file'
import type { VaultView } from './vault'

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export type VaultListResponse = PaginatedResponse<VaultView>
export type FileListResponse = PaginatedResponse<VaultFile>

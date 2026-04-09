import type { VaultFile } from './file'
import type { Vault } from './vault'

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export type VaultListResponse = PaginatedResponse<Vault>
export type FileListResponse = PaginatedResponse<VaultFile>

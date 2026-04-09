import { apiClient } from './client'
import type { FileListResponse, FileStatusResponse, FileUploadResponse } from '@/types'

export const filesApi = {
  list: (vaultId: string) =>
    apiClient.get<FileListResponse>(`/vaults/${vaultId}/files`).then((r) => r.data),

  upload: (vaultId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<FileUploadResponse>(`/vaults/${vaultId}/files`, form).then((r) => r.data)
  },
  getStatus: (vaultId: string, fileId: string) =>
    apiClient
      .get<FileStatusResponse>(`/vaults/${vaultId}/files/${fileId}/status`)
      .then((r) => r.data),

  delete: (vaultId: string, fileId: string) =>
    apiClient.delete(`/vaults/${vaultId}/files/${fileId}`),
}

import { apiClient } from './client'
import type { Vault, VaultCreate, VaultUpdate } from '@/types/vault'
import type { VaultListResponse } from '@/types'

export const vaultsApi = {
  list: (page: number = 1, pageSize: number = 20) =>
    apiClient
      .get<VaultListResponse>('/vaults', { params: { page, page_size: pageSize } })
      .then((r) => r.data),

  get: (id: string) => apiClient.get<Vault>(`/vaults/${id}`).then((r) => r.data),

  create: (data: VaultCreate) => apiClient.post<Vault>('/vaults', data).then((r) => r.data),

  update: (id: string, data: VaultUpdate) =>
    apiClient.put<Vault>(`/vaults/${id}`, data).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/vaults/${id}`),
}

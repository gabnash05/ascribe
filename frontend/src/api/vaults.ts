import { apiClient } from './client'
import type { Vault, VaultListResponse, VaultCreate, VaultUpdate } from '@/types'

export const vaultsApi = {
  list: () => apiClient.get<VaultListResponse[]>('/vaults').then((r) => r.data),

  get: (id: string) => apiClient.get<Vault>(`/vaults/${id}`).then((r) => r.data),

  create: (data: VaultCreate) => apiClient.post<Vault>('/vaults', data).then((r) => r.data),

  update: (id: string, data: VaultUpdate) =>
    apiClient.put<Vault>(`/vaults/${id}`, data).then((r) => r.data),

  delete: (id: string) => apiClient.delete(`/vaults/${id}`),
}

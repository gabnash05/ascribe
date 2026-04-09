export interface Vault {
  id: string
  user_id: string
  name: string
  description: string | null
  vault_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type VaultCreate = Pick<Vault, 'name' | 'description'>
export type VaultUpdate = Partial<VaultCreate>

export interface Vault {
  id: string
  user_id: string
  name: string
  description: string | null
  thumbnail_url: string | null
  vault_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface VaultView extends Vault {
  document_count: number
  flashcard_count: number
  quiz_count: number
  last_studied: Date | null
}

export type VaultCreate = Pick<Vault, 'name' | 'description'>
export type VaultUpdate = Partial<VaultCreate>

import { create } from 'zustand'
import type { VaultView } from '@/types/vault'

type ModalType = 'create' | 'update' | 'delete' | null

interface VaultUIState {
  // Selection
  activeVaultId: string | null
  setActiveVault: (id: string) => void
  clearActiveVault: () => void

  // Generic modal state (more advanced)
  modalType: ModalType
  selectedVault: VaultView | null
  openCreate: () => void
  openUpdate: (vault: VaultView) => void
  openDelete: (vault: VaultView) => void
  closeModal: () => void
}

export const useVaultStore = create<VaultUIState>((set) => ({
  // Selection
  activeVaultId: null,
  setActiveVault: (id) => set({ activeVaultId: id }),
  clearActiveVault: () => set({ activeVaultId: null }),

  // Modal state (single source of truth)
  modalType: null,
  selectedVault: null,

  openCreate: () => set({ modalType: 'create', selectedVault: null }),
  openUpdate: (vault) => set({ modalType: 'update', selectedVault: vault }),
  openDelete: (vault) => set({ modalType: 'delete', selectedVault: vault }),
  closeModal: () => set({ modalType: null, selectedVault: null }),
}))

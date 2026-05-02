import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { vaultsApi } from '@/api/vaults'
import { useVaultStore } from '@/stores/vaultStore'
import type { VaultCreate, VaultUpdate } from '@/types/vault'

// ── Query keys ────────────────────────────────────────────────────────────────

export const vaultKeys = {
  all: () => ['vaults'] as const,
  lists: () => [...vaultKeys.all(), 'list'] as const,
  list: (page: number, pageSize: number) => [...vaultKeys.lists(), { page, pageSize }] as const,
  detail: (id: string) => [...vaultKeys.all(), 'detail', id] as const,
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

export function useVaults(page = 1, pageSize = 20) {
  const setActiveVault = useVaultStore((s) => s.setActiveVault)
  const activeVaultId = useVaultStore((s) => s.activeVaultId)

  return useQuery({
    queryKey: vaultKeys.list(page, pageSize),
    queryFn: async () => {
      const data = await vaultsApi.list(page, pageSize)

      const sortedItems = [...data.items].sort((a, b) => {
        if (!a.last_studied && !b.last_studied) return 0
        if (!a.last_studied) return 1
        if (!b.last_studied) return -1
        return new Date(b.last_studied).getTime() - new Date(a.last_studied).getTime()
      })

      if (!activeVaultId && sortedItems.length > 0) {
        setActiveVault(sortedItems[0].id)
      }

      return {
        ...data,
        vaults: sortedItems,
      }
    },
  })
}

export function useVault(id: string) {
  return useQuery({
    queryKey: vaultKeys.detail(id),
    queryFn: () => vaultsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateVault() {
  const queryClient = useQueryClient()
  const setActiveVault = useVaultStore((s) => s.setActiveVault)

  return useMutation({
    mutationFn: (data: VaultCreate) => vaultsApi.create(data),
    onSuccess: (newVault) => {
      queryClient.setQueriesData<Awaited<ReturnType<typeof vaultsApi.list>>>(
        { queryKey: vaultKeys.lists() },
        (old) => {
          if (!old) return old
          return {
            ...old,
            total: old.total + 1,
            items: [
              {
                ...newVault,
                document_count: 0,
                flashcard_count: 0,
                quiz_count: 0,
                last_studied: null,
              },
              ...old.items,
            ],
          }
        },
      )
      setActiveVault(newVault.id)
      queryClient.invalidateQueries({ queryKey: vaultKeys.lists() })
    },
  })
}

export function useUpdateVault() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: VaultUpdate }) => vaultsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: vaultKeys.lists() })
      queryClient.invalidateQueries({ queryKey: vaultKeys.detail(id) })
    },
  })
}

export function useDeleteVault() {
  const queryClient = useQueryClient()
  const { activeVaultId, setActiveVault, clearActiveVault } = useVaultStore()

  return useMutation({
    mutationFn: (id: string) => vaultsApi.delete(id),
    onSuccess: (_, deletedId) => {
      if (activeVaultId === deletedId) {
        const cached = queryClient.getQueryData<Awaited<ReturnType<typeof vaultsApi.list>>>(
          vaultKeys.lists(),
        )

        const remaining = cached?.items.filter((v) => v.id !== deletedId) ?? []

        if (remaining.length > 0) {
          setActiveVault(remaining[0].id)
        } else {
          clearActiveVault()
        }
      }

      queryClient.invalidateQueries({ queryKey: vaultKeys.lists() })
    },
  })
}

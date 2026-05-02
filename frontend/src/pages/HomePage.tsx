import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { VaultCard } from '@/components/vaults/VaultCard'
import { VaultCardSkeleton } from '@/components/vaults/VaultCardSkeleton'
import { VaultDetail } from '@/components/vaults/VaultDetail'
import { VaultDetailSkeleton } from '@/components/vaults/VaultDetailSkeleton'
import { EmptyState } from '@/components/vaults/EmptyState'
import { CreateVaultDialog } from '@/components/vaults/CreateVaultDialog'
import { UpdateVaultDialog } from '@/components/vaults/UpdateVaultDialog'
import { DeleteVaultDialog } from '@/components/vaults/DeleteVaultDialog'
import { useVaults } from '@/hooks/useVaults'
import { useVaultStore } from '@/stores/vaultStore'

export function HomePage() {
  const { data, isLoading } = useVaults()
  const vaults = data?.vaults ?? []

  const selectedVault = useVaultStore((s) => s.selectedVault)
  const activeVaultId = useVaultStore((s) => s.activeVaultId)
  const setActiveVault = useVaultStore((s) => s.setActiveVault)
  const openCreate = useVaultStore((s) => s.openCreate)

  const activeVault = vaults.find((v) => v.id === activeVaultId) ?? null

  return (
    <>
      <div className="flex h-full overflow-hidden">
        {/* ── Left column ────────────────────────────────────────────── */}
        <div className="flex-1 min-w-0 overflow-y-auto p-6 flex flex-col gap-6">
          <h1 className="text-4xl font-semibold font-heading">What shall we study today?</h1>

          <div className="flex items-center justify-between">
            <p className="text-md font-medium">Your Vaults</p>
            <Button size="lg" className="gap-1.5" onClick={openCreate}>
              <Plus className="h-4 w-4" />
              New Vault
            </Button>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <VaultCardSkeleton key={i} />
              ))}
            </div>
          ) : vaults.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {vaults.map((vault) => (
                <VaultCard
                  key={vault.id}
                  vault={vault}
                  isActive={vault.id === activeVaultId}
                  onClick={() => setActiveVault(vault.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* ── Right column ───────────────────────────────────────────── */}
        <div className="hidden lg:flex lg:w-72 xl:w-80 shrink-0 flex-col border-l bg-card overflow-y-auto">
          <div className="flex-1 p-5">
            {isLoading ? (
              <VaultDetailSkeleton />
            ) : activeVault ? (
              <VaultDetail vault={activeVault} />
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                Select a vault to see details
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ✅ Add all three dialogs */}
      <CreateVaultDialog />
      <UpdateVaultDialog key={selectedVault?.id} />
      <DeleteVaultDialog />
    </>
  )
}

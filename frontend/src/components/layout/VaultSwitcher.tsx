import { ChevronsUpDown, Plus, AlertCircle } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { useVaults } from '@/hooks/useVaults'
import { useVaultStore } from '@/stores/vaultStore'

export function VaultSwitcher() {
  const { isMobile } = useSidebar()
  const { data, isLoading, error } = useVaults() // ← Add error destructuring
  const vaults = data?.items ?? []

  const activeVaultId = useVaultStore((s) => s.activeVaultId)
  const setActiveVault = useVaultStore((s) => s.setActiveVault)
  const openCreate = useVaultStore((s) => s.openCreate)
  const activeVault = vaults.find((v) => v.id === activeVaultId) ?? null

  // ✅ Add loading state
  if (isLoading) {
    return (
      <SidebarMenu>
        <SidebarMenuItem>
          <div className="flex items-center gap-3 px-2 py-1.5">
            <Skeleton className="h-8 w-8 rounded-lg shrink-0" />
            <div className="flex flex-col gap-1.5 flex-1">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-2.5 w-12" />
            </div>
          </div>
        </SidebarMenuItem>
      </SidebarMenu>
    )
  }

  // ✅ Add error state
  if (error) {
    return (
      <SidebarMenu>
        <SidebarMenuItem>
          <div className="flex flex-col gap-2 px-2 py-1.5">
            <div className="flex items-center gap-2 text-destructive text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>Failed to load vaults</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 justify-start text-xs"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        </SidebarMenuItem>
      </SidebarMenu>
    )
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="flex aspect-square h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm shrink-0">
                <span className="font-semibold">
                  {activeVault?.name?.[0]?.toUpperCase() ?? 'V'}
                </span>
              </div>
              <div className="flex flex-col gap-0.5 leading-none min-w-0">
                <span className="font-semibold truncate">
                  {activeVault?.name ?? 'Select a vault'}
                </span>
                <span className="text-xs text-muted-foreground">Vault</span>
              </div>
              <ChevronsUpDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>

          <DropdownMenuContent
            className="w-56"
            align="start"
            side={isMobile ? 'bottom' : 'right'}
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Your Vaults
            </DropdownMenuLabel>

            {vaults.map((vault) => (
              <DropdownMenuItem
                key={vault.id}
                onSelect={() => setActiveVault(vault.id)}
                className="gap-2"
              >
                <span className="truncate">{vault.name}</span>
                {vault.id === activeVaultId && (
                  <span className="ml-auto text-xs text-muted-foreground">Active</span>
                )}
              </DropdownMenuItem>
            ))}

            <DropdownMenuSeparator />

            <DropdownMenuItem className="gap-2 text-muted-foreground" onSelect={openCreate}>
              <Plus className="h-4 w-4" />
              <span>New Vault</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}

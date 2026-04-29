import { useState } from 'react'
import { ChevronsUpDown, Plus } from 'lucide-react'
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

// TODO: replace with real vault data from TanStack Query
const MOCK_VAULTS = [
  { id: '1', name: 'Research Vault' },
  { id: '2', name: 'Personal Notes' },
  { id: '3', name: 'Work Projects' },
]

export function VaultSwitcher() {
  const { isMobile } = useSidebar()
  const [activeVault, setActiveVault] = useState(MOCK_VAULTS[0])

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="flex aspect-square h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm">
                <span className="font-semibold">L</span>
              </div>
              <div className="flex flex-col gap-0.5 leading-none">
                <span className="font-semibold truncate">{activeVault.name}</span>
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

            {MOCK_VAULTS.map((vault) => (
              <DropdownMenuItem
                key={vault.id}
                onSelect={() => setActiveVault(vault)}
                className="gap-2"
              >
                <span className="truncate">{vault.name}</span>
                {vault.id === activeVault.id && (
                  <span className="ml-auto text-xs text-muted-foreground">Active</span>
                )}
              </DropdownMenuItem>
            ))}

            <DropdownMenuSeparator />

            <DropdownMenuItem className="gap-2 text-muted-foreground">
              <Plus className="h-4 w-4" />
              <span>New Vault</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}

import { Link } from '@tanstack/react-router'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from '@/components/ui/sidebar'
import { Home, FileText, Sparkles, Pen, Settings, LogOut } from 'lucide-react'
import { VaultSwitcher } from '@/components/layout/VaultSwitcher'
import { CreateVaultDialog } from '@/components/vaults/CreateVaultDialog'
import { useAuthStore } from '@/stores/authStore'

const navItems = [
  { label: 'Home', to: '/home', icon: Home },
  { label: 'Documents', to: '/documents', icon: FileText },
  { label: 'Generate', to: '/generate', icon: Sparkles },
  { label: 'Workshop', to: '/workshop', icon: Pen },
]

export function AppSidebar() {
  const { signOut } = useAuthStore()

  return (
    <>
      <Sidebar collapsible="icon">
        {/* ── Header — vault switcher ─────────────────────────────────── */}
        <SidebarHeader>
          <VaultSwitcher />
        </SidebarHeader>

        <SidebarSeparator />

        {/* ── Main nav ─────────────────────────────────────────────────── */}
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel className="text-sm">Workspace</SidebarGroupLabel>
            <SidebarMenu>
              {navItems.map(({ label, to, icon: Icon }) => (
                <SidebarMenuItem key={to}>
                  <SidebarMenuButton asChild tooltip={label}>
                    <Link
                      to={to}
                      activeProps={{
                        className: 'bg-sidebar-accent text-sidebar-accent-foreground',
                      }}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="text-sm">{label}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        </SidebarContent>

        {/* ── Footer ───────────────────────────────────────────────────── */}
        <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild tooltip="Settings">
                <Link to="/settings">
                  <Settings className="h-4 w-4 shrink-0" />
                  <span className="text-sm">Settings</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                tooltip="Sign Out"
                onClick={signOut}
                className="text-red-500 hover:text-red-500 hover:bg-red-500/10"
              >
                <LogOut className="h-4 w-4 shrink-0" />
                <span className="text-sm">Sign Out</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>

      <CreateVaultDialog />
    </>
  )
}

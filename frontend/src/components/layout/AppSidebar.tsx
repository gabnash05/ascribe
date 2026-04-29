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
import { Home, FileText, Sparkles, Pen, Settings } from 'lucide-react'
import { VaultSwitcher } from '@/components/layout/VaultSwitcher'
//import { useAuthStore } from '@/stores/authStore'

const navItems = [
  { label: 'Home', to: '/home', icon: Home },
  { label: 'Documents', to: '/documents', icon: FileText },
  { label: 'Generate', to: '/generate', icon: Sparkles },
  { label: 'Workshop', to: '/workshop', icon: Pen },
]

export function AppSidebar() {
  //const { signOut } = useAuthStore()

  return (
    <Sidebar collapsible="icon">
      {/* ── Header — vault switcher ─────────────────────────────────────── */}
      <SidebarHeader>
        <VaultSwitcher />
      </SidebarHeader>

      <SidebarSeparator />

      {/* ── Main nav ───────────────────────────────────────────────────── */}
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarMenu>
            {navItems.map(({ label, to, icon: Icon }) => (
              <SidebarMenuItem key={to}>
                <SidebarMenuButton asChild tooltip={label}>
                  <Link
                    to={to}
                    activeProps={{ className: 'bg-sidebar-accent text-sidebar-accent-foreground' }}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{label}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      {/* ── Footer — settings ──────────────────────────────────────────── */}
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Settings">
              <Link to="/settings">
                <Settings className="h-4 w-4 shrink-0" />
                <span>Settings</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}

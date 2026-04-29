import { useEffect, useState } from 'react'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { LogOut, Settings, User, Search } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { VaultBreadcrumb } from '@/components/layout/VaultBreadcrumb'

export function AppTopbar() {
  const { user, signOut } = useAuthStore()
  const [searchOpen, setSearchOpen] = useState(false)

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setSearchOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const initials =
    user?.user_metadata?.full_name
      ?.split(' ')
      .map((n: string) => n[0])
      .join('')
      .toUpperCase() || '?'

  return (
    <>
      <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
        {/* Left — sidebar trigger + breadcrumb */}
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="h-4" />
        <VaultBreadcrumb />

        {/* Center — compact search button */}
        <div className="flex flex-1 justify-center px-6">
          <button
            onClick={() => setSearchOpen(true)}
            className="
              flex items-center gap-2
              h-8 px-3 rounded-md w-full max-w-100
              bg-muted/60 hover:bg-muted
              border border-border/50 hover:border-border
              text-xs text-muted-foreground
              transition-colors duration-150
              focus:outline-none focus-visible:ring-2 focus-visible:ring-ring
            "
          >
            <Search className="h-3.5 w-3.5 shrink-0" />
            <span className="flex-1 text-left">Search vault…</span>
            <kbd className="hidden sm:inline-flex items-center rounded border border-border bg-background px-1 py-0.5 text-xs font-mono">
              ⌘K
            </kbd>
          </button>
        </div>

        {/* Right — avatar menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Avatar className="h-8 w-8 cursor-pointer">
              <AvatarImage
                src={user?.user_metadata?.avatar_url}
                alt={user?.user_metadata?.full_name ?? 'User'}
              />
              <AvatarFallback className="text-xs">{initials}</AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col gap-0.5">
                <span className="font-medium truncate">
                  {user?.user_metadata?.full_name ?? 'User'}
                </span>
                <span className="text-xs text-muted-foreground truncate">{user?.email}</span>
              </div>
            </DropdownMenuLabel>

            <DropdownMenuSeparator />

            <DropdownMenuItem className="gap-2">
              <User className="h-4 w-4" />
              Profile
            </DropdownMenuItem>

            <DropdownMenuItem className="gap-2">
              <Settings className="h-4 w-4" />
              Settings
            </DropdownMenuItem>

            <DropdownMenuSeparator />

            <DropdownMenuItem
              className="gap-2 text-destructive focus:text-destructive"
              onSelect={signOut}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      {/* Command palette dialog */}
      {searchOpen && (
        <CommandDialog open={searchOpen} onOpenChange={setSearchOpen}>
          <CommandInput placeholder="Search documents, notes, summaries…" />
          <CommandList>
            <CommandEmpty>No results found.</CommandEmpty>
            <CommandGroup heading="Documents">
              <CommandItem>Research Paper — Attention Is All You Need</CommandItem>
              <CommandItem>Lecture Notes — Week 4</CommandItem>
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup heading="Summaries">
              <CommandItem>Summary — Transformer Architecture</CommandItem>
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup heading="Notes">
              <CommandItem>My notes on backpropagation</CommandItem>
            </CommandGroup>
          </CommandList>
        </CommandDialog>
      )}
    </>
  )
}

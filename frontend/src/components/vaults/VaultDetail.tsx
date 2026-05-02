import { Link } from '@tanstack/react-router'
import { BookOpen, FileText, Layers, HelpCircle, ArrowRight, MoreHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { VaultView } from '@/types/vault'
import { formatLastStudied } from '@/lib/vaultUtils'
import { useVaultStore } from '@/stores/vaultStore'

interface VaultDetailProps {
  vault: VaultView
}

export function VaultDetail({ vault }: VaultDetailProps) {
  const openUpdateModal = useVaultStore((s) => s.openUpdate)
  const openDeleteModal = useVaultStore((s) => s.openDelete)

  return (
    <div className="h-full flex flex-col">
      {/* Thumbnail */}
      <div className="relative h-40 w-full bg-muted">
        {vault.thumbnail_url ? (
          <img src={vault.thumbnail_url} alt={vault.name} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <BookOpen className="h-12 w-12 text-muted-foreground/20" />
          </div>
        )}

        {/* Top-right menu overlay */}
        <div className="absolute top-2 right-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="secondary" size="icon" className="h-8 w-8 backdrop-blur">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => openUpdateModal(vault)}>Edit</DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => openDeleteModal(vault)}
                className="text-destructive focus:text-destructive"
              >
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="flex flex-col flex-1 p-0">
        {/* Header */}
        <div className="my-5">
          <h2 className="text-lg font-semibold leading-tight line-clamp-2">{vault.name}</h2>
          <p className="text-xs text-muted-foreground italic mt-1">
            {formatLastStudied(vault.last_studied)}
          </p>
        </div>

        {/* Description */}
        <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3 mb-4">
          {vault.description || 'No description provided.'}
        </p>

        <Separator className="mb-4" />

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 mb-6">
          <Stat icon={<FileText className="h-4 w-4" />} label="Docs" value={vault.document_count} />
          <Stat icon={<Layers className="h-4 w-4" />} label="Cards" value={vault.flashcard_count} />
          <Stat
            icon={<HelpCircle className="h-4 w-4" />}
            label="Quizzes"
            value={vault.quiz_count}
          />
        </div>

        {/* CTA */}
        <div className="mt-auto">
          <Button asChild size="lg" className="w-full gap-2">
            <Link to={`/workshop/${vault.id}`}>
              Continue Studying
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg bg-muted/50 py-3 text-center">
      <div className="text-muted-foreground mb-1">{icon}</div>
      <p className="text-base font-semibold">{value}</p>
      <p className="text-[10px] text-muted-foreground">{label}</p>
    </div>
  )
}

import { BookOpen, Clock } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { VaultView } from '@/types/vault'
import { formatLastStudied } from '@/lib/vaultUtils'

interface VaultCardProps {
  vault: VaultView
  isActive: boolean
  onClick: () => void
}

export function VaultCard({ vault, isActive, onClick }: VaultCardProps) {
  return (
    <Card
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
      tabIndex={0}
      role="button"
      className={`
        overflow-hidden cursor-pointer transition-all duration-150
        hover:shadow-md hover:-translate-y-0.5
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
        ${isActive ? 'ring-1 ring-primary shadow-md' : 'ring-0'}
      `}
    >
      {' '}
      <div className="h-28 bg-muted relative overflow-hidden">
        {vault.thumbnail_url ? (
          <img src={vault.thumbnail_url} alt={vault.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <BookOpen className="h-8 w-8 text-muted-foreground/30" />
          </div>
        )}
        {vault.last_studied && (
          <Badge variant="secondary" className="absolute bottom-2 right-2 text-[10px] gap-1 py-0">
            <Clock className="h-2.5 w-2.5" />
            {formatLastStudied(vault.last_studied)}
          </Badge>
        )}
      </div>
      <CardContent className="p-3 space-y-1">
        <p className="font-medium text-sm leading-tight line-clamp-1">{vault.name}</p>
        <p className="text-xs text-muted-foreground">
          {vault.document_count} {vault.document_count === 1 ? 'document' : 'documents'}
        </p>
      </CardContent>
    </Card>
  )
}

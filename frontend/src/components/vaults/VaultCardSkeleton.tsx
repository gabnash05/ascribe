import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export function VaultCardSkeleton() {
  return (
    <Card className="overflow-hidden" role="status" aria-label="Loading vault card">
      <Skeleton className="h-28 w-full rounded-none" />
      <CardContent className="p-4 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/3" />
      </CardContent>
      <span className="sr-only">Loading...</span>
    </Card>
  )
}

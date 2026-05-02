import { Inbox } from 'lucide-react'

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center gap-4">
      <div className="h-16 w-16 rounded-2xl bg-muted flex items-center justify-center">
        <Inbox className="h-8 w-8 text-muted-foreground/50" />
      </div>
      <div className="space-y-1">
        <p className="font-medium">No vaults yet</p>
        <p className="text-sm text-muted-foreground">
          Create your first vault to start organizing your knowledge.
        </p>
      </div>
    </div>
  )
}

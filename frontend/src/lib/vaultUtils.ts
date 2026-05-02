import type { VaultView } from '@/types/vault'

export function formatLastStudied(date: Date | null): string {
  if (!date) return 'Never studied'
  const diff = Date.now() - date.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

export function sortByLastStudied(vaults: VaultView[]): VaultView[] {
  return [...vaults].sort((a, b) => {
    if (!a.last_studied && !b.last_studied) return 0
    if (!a.last_studied) return 1
    if (!b.last_studied) return -1
    return b.last_studied.getTime() - a.last_studied.getTime()
  })
}

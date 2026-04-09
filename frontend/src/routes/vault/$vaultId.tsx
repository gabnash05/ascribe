import { createFileRoute } from '@tanstack/react-router'
import { VaultPage } from '@/pages/VaultPage'

export const Route = createFileRoute('/vault/$vaultId')({
  component: VaultPage,
})

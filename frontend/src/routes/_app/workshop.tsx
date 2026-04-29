import { createFileRoute } from '@tanstack/react-router'
import { WorkshopPage } from '@/pages/WorkshopPage'

export const Route = createFileRoute('/_app/workshop')({
  component: WorkshopPage,
})

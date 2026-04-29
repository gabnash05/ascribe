import { createFileRoute } from '@tanstack/react-router'
import { GeneratePage } from '@/pages/GeneratePage'

export const Route = createFileRoute('/_app/generate')({
  component: GeneratePage,
})

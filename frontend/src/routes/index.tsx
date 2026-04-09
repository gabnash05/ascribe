import { createFileRoute, redirect } from '@tanstack/react-router'
import { useAuthStore } from '../stores/authStore'

export const Route = createFileRoute('/')({
  beforeLoad: () => {
    const { session } = useAuthStore.getState()
    throw redirect({ to: session ? '/dashboard' : '/login' })
  },
  component: () => null,
})

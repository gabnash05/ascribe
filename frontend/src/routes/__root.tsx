import { createRootRoute, Outlet, redirect } from '@tanstack/react-router'
import { useAuthStore } from '../stores/authStore'
import { NavigationMenu } from '@/components/ui/navigation-menu'

export const Route = createRootRoute({
  beforeLoad: ({ location }) => {
    const { session, isLoading } = useAuthStore.getState()
    const publicPaths = ['/login', '/']
    if (!isLoading && !session && !publicPaths.includes(location.pathname)) {
      throw redirect({ to: '/login', search: { redirect: location.pathname } })
    }
  },
  component: () => (
    <div style={{ fontFamily: 'var(--font-body)' }}>
      <NavigationMenu />
      <Outlet />
    </div>
  ),
})

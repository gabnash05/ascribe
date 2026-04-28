import { createRootRouteWithContext, Outlet, redirect } from '@tanstack/react-router'
import { QueryClient } from '@tanstack/react-query'
import type { Session } from '@supabase/supabase-js'

interface RouterContext {
  queryClient: QueryClient
  session: Session | null
}

export const Route = createRootRouteWithContext<RouterContext>()({
  beforeLoad: ({ location, context }) => {
    const publicPaths = ['/login']
    if (!context.session && !publicPaths.includes(location.pathname)) {
      throw redirect({ to: '/login', search: { redirect: location.pathname } })
    }
  },
  component: () => (
    <div style={{ fontFamily: 'var(--font-body)' }}>
      <Outlet />
    </div>
  ),
})

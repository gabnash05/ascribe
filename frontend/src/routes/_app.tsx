import { createFileRoute, Outlet } from '@tanstack/react-router'
import { NavigationMenu } from '@/components/ui/navigation-menu'

export const Route = createFileRoute('/_app')({
  component: () => (
    <>
      <NavigationMenu />
      <Outlet />
    </>
  ),
})

import { Link, useRouterState } from '@tanstack/react-router'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'

// Maps route pathnames to human-readable labels
const ROUTE_LABELS: Record<string, string> = {
  home: 'Home',
  documents: 'Documents',
  generate: 'Generate',
  workshop: 'Workshop',
  settings: 'Settings',
}

export function VaultBreadcrumb() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  const segments = pathname.split('/').filter(Boolean)

  if (segments.length === 0) return null

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {/* Always show Vaults as the root */}
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link to="/home">Vaults</Link>
          </BreadcrumbLink>
        </BreadcrumbItem>

        {segments.map((segment, index) => {
          const isLast = index === segments.length - 1
          const label = ROUTE_LABELS[segment] ?? segment

          return (
            <span key={index} className="contents">
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                {isLast ? (
                  <BreadcrumbPage>{label}</BreadcrumbPage>
                ) : (
                  <BreadcrumbLink asChild>
                    <Link to={`/${segments.slice(0, index + 1).join('/')}`}>{label}</Link>
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </span>
          )
        })}
      </BreadcrumbList>
    </Breadcrumb>
  )
}

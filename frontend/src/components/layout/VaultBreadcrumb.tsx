import { Link, useRouterState } from '@tanstack/react-router'
import {
  Breadcrumb,
  BreadcrumbEllipsis,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'

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

  const middleSegments = segments.slice(0, -1)
  const lastSegment = segments[segments.length - 1]
  const lastLabel = ROUTE_LABELS[lastSegment] ?? lastSegment

  return (
    <Breadcrumb>
      <BreadcrumbList className="flex-nowrap overflow-hidden">
        {/* Root — always visible */}
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link to="/home">Vaults</Link>
          </BreadcrumbLink>
        </BreadcrumbItem>

        {middleSegments.length > 0 && (
          <>
            {/* Ellipsis — mobile only */}
            <BreadcrumbSeparator className="md:hidden" />
            <BreadcrumbItem className="md:hidden">
              <BreadcrumbEllipsis />
            </BreadcrumbItem>

            {/* Full middle segments — desktop only */}
            {middleSegments.map((segment, index) => (
              <span key={index} className="hidden md:flex md:items-center md:gap-1.5">
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbLink asChild>
                    <Link to={`/${segments.slice(0, index + 1).join('/')}`}>
                      {ROUTE_LABELS[segment] ?? segment}
                    </Link>
                  </BreadcrumbLink>
                </BreadcrumbItem>
              </span>
            ))}
          </>
        )}

        {/* Last segment — always visible */}
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage className="truncate max-w-40">{lastLabel}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  )
}

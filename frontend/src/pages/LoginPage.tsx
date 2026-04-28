import { useState } from 'react'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'
import { FcGoogle } from 'react-icons/fc'
import { SiGithub, SiApple } from 'react-icons/si'
import { useAuthStore } from '@/stores/authStore'

// ─── Replace this URL with your actual hero image ───────────────────────────
const HERO_IMAGE_URL = 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=1200&q=80'

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { signInWithGoogle } = useAuthStore()

  async function handleGoogleSignIn() {
    try {
      setIsLoading(true)
      setError(null)
      await signInWithGoogle()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-in failed.')
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <div
        className="
        w-full md:w-2/5
        flex flex-col items-center justify-center
        px-8 py-16 md:py-0
        bg-background
        min-h-[60vh] md:min-h-screen
      "
      >
        <div className="w-full max-w-xs space-y-8 p-5">
          <div className="space-y-1">
            <h1 className="text-4xl font-semibold tracking-tight">AScribe</h1>
            <p className="text-sm text-muted-foreground">Your personal knowledge workshop</p>
          </div>

          <div className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-base font-medium">Welcome back</h2>
              <p className="text-xs text-muted-foreground">Sign in to access your vaults</p>
            </div>

            <Separator />

            {error && (
              <p className="text-xs text-destructive text-center rounded-md bg-destructive/10 px-3 py-2">
                {error}
              </p>
            )}

            {/* Google — active */}
            <Button
              variant="outline"
              className="w-full gap-2"
              onClick={handleGoogleSignIn}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin shrink-0" />
              ) : (
                <FcGoogle className="h-4 w-4 shrink-0" />
              )}
              {isLoading ? 'Redirecting…' : 'Continue with Google'}
            </Button>

            {/* Placeholder providers — UI only, not yet wired */}
            <Button variant="outline" className="w-full gap-2" disabled>
              <SiGithub className="h-4 w-4 shrink-0" />
              Continue with GitHub
            </Button>

            <Button variant="outline" className="w-full gap-2" disabled>
              <SiApple className="h-4 w-4 shrink-0" />
              Continue with Apple
            </Button>
          </div>

          {/* Footer */}
          <p className="text-xs text-muted-foreground">
            By continuing, you agree to our{' '}
            <a
              href="/terms"
              className="underline underline-offset-4 hover:text-foreground transition-colors"
            >
              Terms of Service
            </a>{' '}
            and{' '}
            <a
              href="/privacy"
              className="underline underline-offset-4 hover:text-foreground transition-colors"
            >
              Privacy Policy
            </a>
            .
          </p>
        </div>
      </div>

      {/* ── Right panel — 3/5 ─────────────────────────────────────────────── */}
      <div
        className="
        hidden md:block
        md:w-3/5
        relative overflow-hidden
      "
      >
        <img
          src={HERO_IMAGE_URL}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-black/20" />
      </div>
    </div>
  )
}

import { useRef, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useVaultStore } from '@/stores/vaultStore'
import { useUpdateVault } from '@/hooks/useVaults'

export function UpdateVaultDialog() {
  const { modalType, selectedVault, closeModal } = useVaultStore()
  const { mutate: updateVault, isPending } = useUpdateVault()

  const [name, setName] = useState(selectedVault?.name ?? '')
  const [description, setDescription] = useState(selectedVault?.description ?? '')
  const [error, setError] = useState<string | null>(null)
  const nameRef = useRef<HTMLInputElement>(null)

  const isOpen = modalType === 'update'

  function handleSubmit() {
    const trimmed = name.trim()

    if (!trimmed) {
      setError('Vault name is required')
      nameRef.current?.focus()
      return
    }

    if (trimmed.length > 100) {
      setError('Name must be 100 characters or less')
      return
    }

    if (description.length > 500) {
      setError('Description must be 500 characters or less')
      return
    }

    if (!selectedVault) return

    updateVault(
      {
        id: selectedVault.id,
        data: {
          name: trimmed,
          description: description.trim() || null,
        },
      },
      {
        onSuccess: () => closeModal(),
        onError: (err) => setError(err.message || 'Update failed'),
      },
    )
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  if (!selectedVault) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && closeModal()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Vault</DialogTitle>
          <DialogDescription>Update your vault details.</DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="vault-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="vault-name"
              ref={nameRef}
              value={name}
              onChange={(e) => {
                setName(e.target.value)
                if (error) setError(null)
              }}
              onKeyDown={handleKeyDown}
              disabled={isPending}
              placeholder="e.g. Machine Learning, Bar Exam..."
              className={error ? 'border-destructive focus-visible:ring-destructive' : ''}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="vault-description">
              Description
              <span className="ml-1.5 text-xs text-muted-foreground font-normal">optional</span>
            </Label>
            <Textarea
              id="vault-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isPending}
              rows={3}
              className="resize-none"
              placeholder="What's this vault for?"
            />
            <p className="text-xs text-muted-foreground text-right">{description.length}/500</p>
          </div>

          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={closeModal} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isPending || !name.trim()}>
            {isPending ? 'Saving…' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

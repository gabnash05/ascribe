import { useEffect, useRef, useState } from 'react'
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
import { useCreateVault } from '@/hooks/useVaults'

export function CreateVaultDialog() {
  const { modalType, closeModal, selectedVault } = useVaultStore()
  const { mutate: createVault, isPending } = useCreateVault()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [nameError, setNameError] = useState<string | null>(null)
  const nameRef = useRef<HTMLInputElement>(null)

  const isOpen = modalType === 'create'

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => nameRef.current?.focus(), 50)
    }
  }, [isOpen])

  function handleSubmit() {
    const trimmedName = name.trim()

    if (!trimmedName) {
      setNameError('Vault name is required')
      nameRef.current?.focus()
      return
    }
    if (trimmedName.length > 100) {
      setNameError('Name must be 100 characters or less')
      return
    }
    if (description.trim().length > 500) {
      setNameError('Description must be 500 characters or less')
      return
    }

    createVault(
      {
        name: trimmedName,
        description: description.trim() || null,
      },
      {
        onSuccess: () => closeModal(),
        onError: (error) => {
          const errorMessage = error.message || 'Something went wrong. Please try again.'
          setNameError(errorMessage)
        },
      },
    )
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && closeModal()}>
      <DialogContent key={selectedVault?.id ?? 'create'} className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New Vault</DialogTitle>
          <DialogDescription>
            A vault holds your documents and everything generated from them.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">
          {/* Name */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="vault-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="vault-name"
              ref={nameRef}
              placeholder="e.g. Machine Learning, Bar Exam..."
              value={name}
              onChange={(e) => {
                setName(e.target.value)
                if (nameError) setNameError(null)
              }}
              onKeyDown={handleKeyDown}
              disabled={isPending}
              className={nameError ? 'border-destructive focus-visible:ring-destructive' : ''}
            />
            {nameError && <p className="text-xs text-destructive">{nameError}</p>}
          </div>

          {/* Description */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="vault-description">
              Description
              <span className="ml-1.5 text-xs text-muted-foreground font-normal">optional</span>
            </Label>
            <Textarea
              id="vault-description"
              placeholder="What's this vault for?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isPending}
              rows={3}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground text-right">{description.length}/500</p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={closeModal} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isPending || !name.trim()}>
            {isPending ? 'Creating…' : 'Create Vault'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

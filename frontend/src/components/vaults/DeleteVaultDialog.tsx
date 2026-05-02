import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useVaultStore } from '@/stores/vaultStore'
import { useDeleteVault } from '@/hooks/useVaults'

export function DeleteVaultDialog() {
  const { modalType, selectedVault, closeModal } = useVaultStore()
  const { mutate: deleteVault, isPending } = useDeleteVault()

  const isOpen = modalType === 'delete'

  function handleDelete() {
    if (!selectedVault) return

    deleteVault(selectedVault.id, {
      onSuccess: () => {
        closeModal()
      },
    })
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && closeModal()}>
      <DialogContent key={selectedVault?.id} className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Vault</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete{' '}
            <span className="font-medium text-foreground">{selectedVault?.name}</span> and all of
            its contents.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button variant="outline" onClick={closeModal} disabled={isPending}>
            Cancel
          </Button>

          <Button variant="destructive" onClick={handleDelete} disabled={isPending}>
            {isPending ? 'Deleting…' : 'Delete Vault'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

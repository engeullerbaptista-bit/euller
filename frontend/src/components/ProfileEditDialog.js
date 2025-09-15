import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { Separator } from './ui/separator';
import { toast } from 'sonner';
import { Edit } from 'lucide-react';

// Profile Edit Dialog Component
function ProfileEditDialog({ user, onUpdate }) {
  const [isOpen, setIsOpen] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { updateProfile } = React.useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Validation
    if (newPassword && newPassword !== confirmPassword) {
      toast.error('As senhas não coincidem');
      setLoading(false);
      return;
    }

    if (newPassword && !currentPassword) {
      toast.error('Digite sua senha atual para alterar a senha');
      setLoading(false);
      return;
    }

    const updateData = {};
    
    if (fullName !== user.full_name) {
      updateData.full_name = fullName;
    }

    if (newPassword) {
      updateData.current_password = currentPassword;
      updateData.new_password = newPassword;
    }

    if (Object.keys(updateData).length === 0) {
      toast.info('Nenhuma alteração foi feita');
      setLoading(false);
      return;
    }

    const success = await updateProfile(updateData);
    if (success) {
      setIsOpen(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      if (onUpdate) onUpdate();
    }
    
    setLoading(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="text-amber-700 hover:text-amber-800">
          <Edit className="w-4 h-4 mr-1" />
          Editar Perfil
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-white border-amber-200">
        <DialogHeader>
          <DialogTitle className="text-amber-900 font-serif">Editar Perfil</DialogTitle>
          <DialogDescription className="text-amber-700">
            Atualize suas informações pessoais
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName" className="text-amber-900 font-medium">Nome Completo</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="border-amber-300 focus:border-amber-500"
                placeholder="Seu nome completo"
              />
            </div>

            <Separator />
            
            <div className="space-y-2">
              <Label className="text-amber-900 font-medium">Alterar Senha (opcional)</Label>
              
              <Input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="border-amber-300 focus:border-amber-500"
                placeholder="Senha atual"
              />
              
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="border-amber-300 focus:border-amber-500"
                placeholder="Nova senha"
              />
              
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="border-amber-300 focus:border-amber-500"
                placeholder="Confirmar nova senha"
              />
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setIsOpen(false)}
              className="border-amber-300"
            >
              Cancelar
            </Button>
            <Button 
              type="submit" 
              className="bg-amber-700 hover:bg-amber-800"
              disabled={loading}
            >
              {loading ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default ProfileEditDialog;
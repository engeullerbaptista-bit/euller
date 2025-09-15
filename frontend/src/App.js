import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Import shadcn components
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Separator } from './components/ui/separator';
import { Textarea } from './components/ui/textarea';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';

// Icons
import { Eye, Upload, Download, Trash2, Shield, Users, FileText, LogOut, Crown, Star, Circle, KeyRound, Edit, User, ExternalLink } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      toast.success('Login realizado com sucesso!');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro no login';
      toast.error(message);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    toast.info('Logout realizado com sucesso');
  };

  const register = async (userData) => {
    try {
      await axios.post(`${API}/register`, userData);
      toast.success('Cadastro realizado! Aguarde aprovação do administrador.');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro no cadastro';
      toast.error(message);
      return false;
    }
  };

  const forgotPassword = async (email) => {
    try {
      await axios.post(`${API}/forgot-password`, { email });
      toast.success('Se o email estiver cadastrado, você receberá instruções para redefinir a senha.');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao solicitar recuperação de senha';
      toast.error(message);
      return false;
    }
  };

  const resetPassword = async (email, resetToken, newPassword) => {
    try {
      await axios.post(`${API}/reset-password`, {
        email,
        reset_token: resetToken,
        new_password: newPassword
      });
      toast.success('Senha redefinida com sucesso!');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao redefinir senha';
      toast.error(message);
      return false;
    }
  };

  const updateProfile = async (updateData) => {
    try {
      await axios.put(`${API}/me`, updateData);
      await fetchUserInfo(); // Refresh user data
      toast.success('Perfil atualizado com sucesso!');
      return true;
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao atualizar perfil';
      toast.error(message);
      return false;
    }
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      logout, 
      register, 
      forgotPassword, 
      resetPassword, 
      updateProfile,
      loading 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

// Login Component
function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [level, setLevel] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register, forgotPassword, resetPassword } = React.useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    if (isForgotPassword) {
      if (resetToken) {
        // Reset password
        await resetPassword(email, resetToken, newPassword);
        setIsForgotPassword(false);
        setResetToken('');
        setNewPassword('');
      } else {
        // Request password reset
        await forgotPassword(email);
      }
    } else if (isLogin) {
      await login(email, password);
    } else {
      if (!fullName || !level) {
        toast.error('Preencha todos os campos');
        setLoading(false);
        return;
      }
      const success = await register({
        email,
        password,
        full_name: fullName,
        level: parseInt(level)
      });
      if (success) {
        setIsLogin(true);
        setEmail('');
        setPassword('');
        setFullName('');
        setLevel('');
      }
    }
    setLoading(false);
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setFullName('');
    setLevel('');
    setResetToken('');
    setNewPassword('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-900 via-amber-800 to-yellow-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 opacity-20" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
      }}></div>
      
      <Card className="w-full max-w-md bg-white/95 backdrop-blur-sm shadow-2xl border-amber-200">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-amber-700 rounded-full flex items-center justify-center mb-4">
            <Shield className="w-8 h-8 text-amber-100" />
          </div>
          <CardTitle className="text-2xl font-serif text-amber-900">
            R:.L:. VASCO DA GAMA Nº12
          </CardTitle>
          <CardDescription className="text-amber-700">
            {isForgotPassword 
              ? 'Recuperação de Senha' 
              : isLogin 
                ? 'Acesso Restrito aos Irmãos' 
                : 'Solicitação de Acesso'
            }
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-amber-900 font-medium">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="border-amber-300 focus:border-amber-500"
                placeholder="seu@email.com"
              />
            </div>

            {isForgotPassword && resetToken ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="resetToken" className="text-amber-900 font-medium">Token de Recuperação</Label>
                  <Input
                    id="resetToken"
                    type="text"
                    value={resetToken}
                    onChange={(e) => setResetToken(e.target.value)}
                    required
                    className="border-amber-300 focus:border-amber-500"
                    placeholder="Cole o token recebido por email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="newPassword" className="text-amber-900 font-medium">Nova Senha</Label>
                  <Input
                    id="newPassword"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    className="border-amber-300 focus:border-amber-500"
                    placeholder="••••••••"
                  />
                </div>
              </>
            ) : !isForgotPassword && (
              <div className="space-y-2">
                <Label htmlFor="password" className="text-amber-900 font-medium">Senha</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required={!isForgotPassword}
                  className="border-amber-300 focus:border-amber-500"
                  placeholder="••••••••"
                />
              </div>
            )}

            {!isLogin && !isForgotPassword && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="fullName" className="text-amber-900 font-medium">Nome Completo</Label>
                  <Input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required={!isLogin && !isForgotPassword}
                    className="border-amber-300 focus:border-amber-500"
                    placeholder="Seu nome completo"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="level" className="text-amber-900 font-medium">Grau Maçônico</Label>
                  <Select value={level} onValueChange={setLevel} required={!isLogin && !isForgotPassword}>
                    <SelectTrigger className="border-amber-300 focus:border-amber-500">
                      <SelectValue placeholder="Selecione seu grau" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">
                        <div className="flex items-center gap-2">
                          <Circle className="w-4 h-4" />
                          Aprendiz
                        </div>
                      </SelectItem>
                      <SelectItem value="2">
                        <div className="flex items-center gap-2">
                          <Star className="w-4 h-4" />
                          Companheiro
                        </div>
                      </SelectItem>
                      <SelectItem value="3">
                        <div className="flex items-center gap-2">
                          <Crown className="w-4 h-4" />
                          Mestre
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full bg-amber-700 hover:bg-amber-800 text-white"
              disabled={loading}
            >
              {loading ? 'Processando...' : 
               isForgotPassword ? 
                 (resetToken ? 'Redefinir Senha' : 'Enviar Link de Recuperação') :
                 (isLogin ? 'Entrar' : 'Solicitar Acesso')
              }
            </Button>

            <div className="flex flex-col space-y-2 w-full">
              {!isForgotPassword && (
                <>
                  <Button
                    type="button"
                    variant="ghost"
                    className="text-amber-700 hover:text-amber-800"
                    onClick={() => {
                      setIsLogin(!isLogin);
                      resetForm();
                    }}
                  >
                    {isLogin ? 'Solicitar novo acesso' : 'Já tenho acesso'}
                  </Button>

                  {isLogin && (
                    <Button
                      type="button"
                      variant="ghost"
                      className="text-amber-600 hover:text-amber-700 flex items-center gap-2"
                      onClick={() => {
                        setIsForgotPassword(true);
                        resetForm();
                      }}
                    >
                      <KeyRound className="w-4 h-4" />
                      Esqueci minha senha
                    </Button>
                  )}
                </>
              )}

              {isForgotPassword && (
                <>
                  <Button
                    type="button"
                    variant="ghost"
                    className="text-amber-700 hover:text-amber-800"
                    onClick={() => {
                      setIsForgotPassword(false);
                      setIsLogin(true);
                      resetForm();
                    }}
                  >
                    Voltar ao login
                  </Button>

                  {!resetToken && (
                    <Button
                      type="button"
                      variant="ghost"
                      className="text-amber-600 hover:text-amber-700"
                      onClick={() => setResetToken('token_placeholder')}
                    >
                      Já tenho o token de recuperação
                    </Button>
                  )}
                </>
              )}
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

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

// Dashboard Component
function Dashboard() {
  const { user, logout } = React.useContext(AuthContext);
  const [works, setWorks] = useState({});
  const [pendingUsers, setPendingUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [uploadLevel, setUploadLevel] = useState('');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadFile, setUploadFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const isAdmin = user?.email === 'engeullerbaptista@gmail.com' || user?.email === 'admin@admin.com';
  const canDeleteWorks = isAdmin || user?.level === 3; // Admin or Master can delete

  useEffect(() => {
    loadWorks();
    if (isAdmin) {
      loadPendingUsers();
      loadAllUsers();
    }
  }, [isAdmin]);

  const loadWorks = async () => {
    try {
      const response = await axios.get(`${API}/works`);
      setWorks(response.data);
    } catch (error) {
      toast.error('Erro ao carregar trabalhos');
    }
  };

  const loadPendingUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/pending-users`);
      setPendingUsers(response.data);
    } catch (error) {
      toast.error('Erro ao carregar usuários pendentes');
    }
  };

  const loadAllUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/all-users`);
      setAllUsers(response.data);
    } catch (error) {
      toast.error('Erro ao carregar usuários');
    }
  };

  const approveUser = async (userId) => {
    try {
      await axios.post(`${API}/admin/approve-user/${userId}`);
      toast.success('Usuário aprovado com sucesso');
      loadPendingUsers();
      loadAllUsers();
    } catch (error) {
      toast.error('Erro ao aprovar usuário');
    }
  };

  const rejectUser = async (userId) => {
    try {
      await axios.post(`${API}/admin/reject-user/${userId}`);
      toast.success('Usuário rejeitado');
      loadPendingUsers();
      loadAllUsers();
    } catch (error) {
      toast.error('Erro ao rejeitar usuário');
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm('Tem certeza que deseja deletar este usuário?')) return;
    
    try {
      await axios.delete(`${API}/admin/delete-user/${userId}`);
      toast.success('Usuário deletado com sucesso');
      loadAllUsers();
    } catch (error) {
      toast.error('Erro ao deletar usuário');
    }
  };

  const deleteWork = async (workId) => {
    if (!window.confirm('Tem certeza que deseja deletar este trabalho?')) return;
    
    try {
      await axios.delete(`${API}/delete-work/${workId}`);
      toast.success('Trabalho deletado com sucesso');
      loadWorks();
    } catch (error) {
      toast.error('Erro ao deletar trabalho');
    }
  };

  const viewWork = (workId) => {
    // Open PDF in new tab for viewing
    const viewUrl = `${API}/work-file/${workId}`;
    window.open(viewUrl, '_blank');
  };

  const downloadWork = (workId) => {
    // Download PDF file
    const downloadUrl = `${API}/download-work/${workId}`;
    window.open(downloadUrl, '_blank');
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle || !uploadLevel) {
      toast.error('Preencha todos os campos');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('title', uploadTitle);

    try {
      const response = await axios.post(`${API}/upload-work/${uploadLevel}?title=${encodeURIComponent(uploadTitle)}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast.success('Trabalho enviado com sucesso!');
      setUploadDialog(false);
      setUploadTitle('');
      setUploadFile(null);
      setUploadLevel('');
      loadWorks();
      
      // Show uploaded work immediately if file_id is returned
      if (response.data.file_id) {
        setTimeout(() => {
          viewWork(response.data.file_id);
        }, 1000);
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao enviar trabalho';
      toast.error(message);
    }
    setLoading(false);
  };

  const getLevelIcon = (level) => {
    switch (level) {
      case 1: return <Circle className="w-4 h-4" />;
      case 2: return <Star className="w-4 h-4" />;
      case 3: return <Crown className="w-4 h-4" />;
      default: return <Circle className="w-4 h-4" />;
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 1: return 'bg-blue-100 text-blue-800 border-blue-200';
      case 2: return 'bg-green-100 text-green-800 border-green-200';
      case 3: return 'bg-amber-100 text-amber-800 border-amber-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-yellow-50">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-sm border-b border-amber-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-700 rounded-full flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-serif font-bold text-amber-900">R:.L:. VASCO DA GAMA Nº12</h1>
                <p className="text-sm text-amber-700">Acesso Restrito</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-amber-900">{user.full_name}</p>
                <Badge variant="outline" className={getLevelColor(user.level)}>
                  {getLevelIcon(user.level)}
                  <span className="ml-1 capitalize">{user.level_name}</span>
                </Badge>
              </div>
              <ProfileEditDialog user={user} />
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={logout}
                className="text-amber-700 hover:text-amber-800"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="works" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 bg-white/80 border border-amber-200">
            <TabsTrigger value="works" className="data-[state=active]:bg-amber-100">
              <FileText className="w-4 h-4 mr-2" />
              Trabalhos
            </TabsTrigger>
            <TabsTrigger value="upload" className="data-[state=active]:bg-amber-100">
              <Upload className="w-4 h-4 mr-2" />
              Enviar
            </TabsTrigger>
            {isAdmin && (
              <>
                <TabsTrigger value="pending" className="data-[state=active]:bg-amber-100">
                  <Users className="w-4 h-4 mr-2" />
                  Aprovações
                  {pendingUsers.length > 0 && (
                    <Badge className="ml-2 bg-red-500">{pendingUsers.length}</Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="admin" className="data-[state=active]:bg-amber-100">
                  <Shield className="w-4 h-4 mr-2" />
                  Admin
                </TabsTrigger>
              </>
            )}
          </TabsList>

          {/* Works Tab */}
          <TabsContent value="works" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-serif font-bold text-amber-900">Trabalhos Maçônicos</h2>
            </div>

            <div className="grid gap-6">
              {['aprendiz', 'companheiro', 'mestre'].map((levelName, index) => {
                const levelNum = index + 1;
                const levelWorks = works[levelName] || [];
                
                // Check if user can access this level
                if (user.level < levelNum) return null;

                return (
                  <Card key={levelName} className="bg-white/80 border-amber-200">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-3 text-amber-900">
                        {getLevelIcon(levelNum)}
                        <span className="capitalize font-serif">{levelName}</span>
                        <Badge variant="outline" className={getLevelColor(levelNum)}>
                          {levelWorks.length} trabalhos
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {levelWorks.length === 0 ? (
                        <p className="text-amber-600 italic">Nenhum trabalho disponível neste grau.</p>
                      ) : (
                        <div className="grid gap-3">
                          {levelWorks.map((work) => (
                            <div key={work.id} className="flex items-center justify-between p-3 bg-amber-50 rounded-lg border border-amber-100">
                              <div className="flex-1">
                                <h4 className="font-medium text-amber-900">{work.title}</h4>
                                <p className="text-sm text-amber-600">
                                  Por: {work.uploaded_by_name} • {new Date(work.uploaded_at).toLocaleDateString('pt-BR')}
                                </p>
                              </div>
                              <div className="flex items-center gap-2">
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  className="border-amber-300 text-amber-700"
                                  onClick={() => viewWork(work.id)}
                                >
                                  <ExternalLink className="w-4 h-4 mr-1" />
                                  Visualizar
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  className="border-amber-300 text-amber-700"
                                  onClick={() => downloadWork(work.id)}
                                >
                                  <Download className="w-4 h-4 mr-1" />
                                  Baixar
                                </Button>
                                {canDeleteWorks && (
                                  <Button 
                                    size="sm" 
                                    variant="outline" 
                                    className="border-red-300 text-red-700"
                                    onClick={() => deleteWork(work.id)}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload">
            <Card className="bg-white/80 border-amber-200">
              <CardHeader>
                <CardTitle className="text-amber-900 font-serif">Enviar Trabalho</CardTitle>
                <CardDescription className="text-amber-700">
                  Compartilhe seus trabalhos maçônicos com os irmãos
                </CardDescription>
              </CardHeader>
              <form onSubmit={handleUpload}>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="title" className="text-amber-900 font-medium">Título do Trabalho</Label>
                    <Input
                      id="title"
                      value={uploadTitle}
                      onChange={(e) => setUploadTitle(e.target.value)}
                      placeholder="Ex: Simbolismo da Acácia"
                      className="border-amber-300 focus:border-amber-500"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="level" className="text-amber-900 font-medium">Grau</Label>
                    <Select value={uploadLevel} onValueChange={setUploadLevel} required>
                      <SelectTrigger className="border-amber-300 focus:border-amber-500">
                        <SelectValue placeholder="Selecione o grau" />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3].map(level => {
                          if (user.level < level) return null;
                          const levelName = ['aprendiz', 'companheiro', 'mestre'][level - 1];
                          return (
                            <SelectItem key={level} value={level.toString()}>
                              <div className="flex items-center gap-2">
                                {getLevelIcon(level)}
                                <span className="capitalize">{levelName}</span>
                              </div>
                            </SelectItem>
                          );
                        })}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="file" className="text-amber-900 font-medium">Arquivo PDF</Label>
                    <Input
                      id="file"
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setUploadFile(e.target.files[0])}
                      className="border-amber-300 focus:border-amber-500"
                      required
                    />
                    <p className="text-sm text-amber-600">Apenas arquivos PDF são aceitos</p>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button 
                    type="submit" 
                    className="bg-amber-700 hover:bg-amber-800"
                    disabled={loading}
                  >
                    {loading ? 'Enviando...' : 'Enviar Trabalho'}
                  </Button>
                </CardFooter>
              </form>
            </Card>
          </TabsContent>

          {/* Admin Tabs */}
          {isAdmin && (
            <>
              <TabsContent value="pending">
                <Card className="bg-white/80 border-amber-200">
                  <CardHeader>
                    <CardTitle className="text-amber-900 font-serif">Usuários Pendentes de Aprovação</CardTitle>
                    <CardDescription className="text-amber-700">
                      Solicitações de acesso aguardando sua aprovação
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {pendingUsers.length === 0 ? (
                      <p className="text-amber-600 italic">Nenhuma solicitação pendente.</p>
                    ) : (
                      <div className="space-y-4">
                        {pendingUsers.map((pendingUser) => (
                          <div key={pendingUser.id} className="flex items-center justify-between p-4 bg-amber-50 rounded-lg border border-amber-100">
                            <div className="flex-1">
                              <h4 className="font-medium text-amber-900">{pendingUser.full_name}</h4>
                              <p className="text-sm text-amber-600">{pendingUser.email}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge variant="outline" className={getLevelColor(pendingUser.level)}>
                                  {getLevelIcon(pendingUser.level)}
                                  <span className="ml-1 capitalize">{pendingUser.level_name}</span>
                                </Badge>
                                <span className="text-xs text-amber-500">
                                  {new Date(pendingUser.created_at).toLocaleDateString('pt-BR')}
                                </span>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Button 
                                size="sm" 
                                className="bg-green-600 hover:bg-green-700"
                                onClick={() => approveUser(pendingUser.id)}
                              >
                                Aprovar
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="border-red-300 text-red-700"
                                onClick={() => rejectUser(pendingUser.id)}
                              >
                                Rejeitar
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="admin">
                <Card className="bg-white/80 border-amber-200">
                  <CardHeader>
                    <CardTitle className="text-amber-900 font-serif">Gerenciar Usuários</CardTitle>
                    <CardDescription className="text-amber-700">
                      Administração completa dos usuários do sistema
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {allUsers.map((userItem) => (
                        <div key={userItem.id} className="flex items-center justify-between p-4 bg-amber-50 rounded-lg border border-amber-100">
                          <div className="flex-1">
                            <h4 className="font-medium text-amber-900">{userItem.full_name}</h4>
                            <p className="text-sm text-amber-600">{userItem.email}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="outline" className={getLevelColor(userItem.level)}>
                                {getLevelIcon(userItem.level)}
                                <span className="ml-1 capitalize">{userItem.level_name}</span>
                              </Badge>
                              <Badge 
                                variant={userItem.status === 'approved' ? 'default' : 'secondary'}
                                className={
                                  userItem.status === 'approved' 
                                    ? 'bg-green-100 text-green-800' 
                                    : userItem.status === 'pending'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-red-100 text-red-800'
                                }
                              >
                                {userItem.status === 'approved' ? 'Aprovado' : 
                                 userItem.status === 'pending' ? 'Pendente' : 'Rejeitado'}
                              </Badge>
                              <span className="text-xs text-amber-500">
                                {new Date(userItem.created_at).toLocaleDateString('pt-BR')}
                              </span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            {!['engeullerbaptista@gmail.com', 'admin@admin'].includes(userItem.email) && (
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="border-red-300 text-red-700"
                                onClick={() => deleteUser(userItem.id)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </>
          )}
        </Tabs>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/*" element={<AppContent />} />
          </Routes>
          <Toaster position="top-right" />
        </div>
      </Router>
    </AuthProvider>
  );
}

function AppContent() {
  const { user, loading } = React.useContext(AuthContext);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-900 to-yellow-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-amber-700 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Shield className="w-8 h-8 text-amber-100" />
          </div>
          <p className="text-amber-100">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route 
        path="/" 
        element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} 
      />
      <Route 
        path="/dashboard" 
        element={user ? <Dashboard /> : <Navigate to="/" replace />} 
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
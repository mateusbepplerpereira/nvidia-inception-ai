import { useState, useEffect } from 'react';
import { newsletterService } from '../services/api';

function NewsletterEmails() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingEmail, setEditingEmail] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    name: ''
  });

  useEffect(() => {
    loadEmails();
  }, []);

  const loadEmails = async () => {
    try {
      setLoading(true);
      const data = await newsletterService.getEmails();
      setEmails(data);
    } catch (error) {
      console.error('Erro ao carregar emails:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingEmail) {
        await newsletterService.updateEmail(editingEmail.id, formData);
      } else {
        await newsletterService.addEmail(formData);
      }

      setShowModal(false);
      setEditingEmail(null);
      setFormData({ email: '', name: '' });
      loadEmails();
    } catch (error) {
      console.error('Erro ao salvar email:', error);
      alert('Erro ao salvar email. Verifique se o email não está duplicado.');
    }
  };

  const handleEdit = (email) => {
    setEditingEmail(email);
    setFormData({
      email: email.email,
      name: email.name || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (emailId) => {
    if (window.confirm('Tem certeza que deseja remover este email da newsletter?')) {
      try {
        await newsletterService.deleteEmail(emailId);
        loadEmails();
      } catch (error) {
        console.error('Erro ao deletar email:', error);
      }
    }
  };

  const handleToggle = async (emailId) => {
    try {
      await newsletterService.toggleEmail(emailId);
      loadEmails();
    } catch (error) {
      console.error('Erro ao alterar status do email:', error);
    }
  };


  const formatDate = (dateString) => {
    if (!dateString) return 'Não informado';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-nvidia-green text-lg">Carregando emails...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header da Seção */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Lista de Emails para Newsletter</h2>
          <p className="text-gray-400 text-sm">Gerencie os emails que receberão relatórios automáticos por newsletter</p>
        </div>
        <button
          onClick={() => {
            setEditingEmail(null);
            setFormData({ email: '', name: '' });
            setShowModal(true);
          }}
          className="bg-nvidia-green text-nvidia-dark px-4 py-2 rounded-md hover:bg-green-600 transition-colors flex items-center space-x-2"
        >
          <ion-icon name="add-outline"></ion-icon>
          <span>Novo Email</span>
        </button>
      </div>

      {/* Tabela de Emails */}
      <div className="bg-nvidia-gray rounded-lg overflow-hidden mt-8">
        <div className="px-6 py-4 bg-nvidia-lightGray">
          <h3 className="text-lg font-semibold text-white">Emails Cadastrados ({emails.length})</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-nvidia-lightGray">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Cadastrado em
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nvidia-lightGray">
              {emails.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-gray-400">
                    Nenhum email cadastrado. Clique em "Novo Email" para adicionar.
                  </td>
                </tr>
              ) : (
                emails.map((email) => (
                  <tr key={email.id} className="hover:bg-nvidia-lightGray transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <ion-icon name="mail-outline" class="text-nvidia-green mr-2"></ion-icon>
                        <span className="text-white font-medium">{email.email}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-300">
                      {email.name || 'Não informado'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        email.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {email.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm">
                      {formatDate(email.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleToggle(email.id)}
                          className={`p-1 rounded ${
                            email.is_active
                              ? 'text-yellow-400 hover:text-yellow-300'
                              : 'text-green-400 hover:text-green-300'
                          }`}
                          title={email.is_active ? 'Desativar' : 'Ativar'}
                        >
                          <ion-icon
                            name={email.is_active ? 'pause-outline' : 'play-outline'}
                            size="small"
                          ></ion-icon>
                        </button>
                        <button
                          onClick={() => handleEdit(email)}
                          className="text-blue-400 hover:text-blue-300 p-1 rounded"
                          title="Editar"
                        >
                          <ion-icon name="pencil-outline" size="small"></ion-icon>
                        </button>
                        <button
                          onClick={() => handleDelete(email.id)}
                          className="text-red-400 hover:text-red-300 p-1 rounded"
                          title="Remover"
                        >
                          <ion-icon name="trash-outline" size="small"></ion-icon>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer com estatísticas */}
        {emails.length > 0 && (
          <div className="px-6 py-3 bg-nvidia-lightGray border-t border-nvidia-gray">
            <div className="flex items-center justify-between text-sm text-gray-400">
              <span>
                Total: {emails.length} email(s) •
                Ativos: {emails.filter(e => e.is_active).length} •
                Inativos: {emails.filter(e => !e.is_active).length}
              </span>
              <span className="text-xs">
                <ion-icon name="information-circle-outline" class="mr-1"></ion-icon>
                Apenas emails ativos recebem newsletters
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Modal para Criar/Editar Email */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setShowModal(false)}
        >
          <div
            className="bg-nvidia-gray rounded-lg w-full max-w-md m-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header do Modal */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-nvidia-lightGray">
              <h3 className="text-xl font-semibold text-white">
                {editingEmail ? 'Editar Email' : 'Novo Email'}
              </h3>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <ion-icon name="close-outline" class="text-2xl"></ion-icon>
              </button>
            </div>

            {/* Conteúdo do Modal */}
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                  placeholder="exemplo@empresa.com"
                  disabled={editingEmail} // Não permite editar email, apenas nome
                />
                {editingEmail && (
                  <p className="text-xs text-gray-400 mt-1">
                    O email não pode ser alterado. Para trocar, exclua e crie um novo.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Nome (opcional)
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                  placeholder="Nome da pessoa ou empresa"
                />
              </div>

              {/* Botões */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="bg-nvidia-green text-nvidia-dark px-4 py-2 rounded-md hover:bg-green-600 transition-colors font-medium"
                >
                  {editingEmail ? 'Atualizar' : 'Adicionar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default NewsletterEmails;
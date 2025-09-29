import { useState, useEffect } from 'react';
import { jobsService } from '../services/api';
import '../styles/modal-scroll.css';
import NewsletterEmails from '../components/NewsletterEmails';

function Settings() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    task_type: 'newsletter',
    interval_value: 1,
    interval_unit: 'hours',
    task_config: {
      country: '',
      sector: '',
      limit: 10
    }
  });

  const intervalUnits = [
    { value: 'minutes', label: 'Minutos' },
    { value: 'hours', label: 'Horas' },
    { value: 'days', label: 'Dias' },
    { value: 'weeks', label: 'Semanas' },
    { value: 'months', label: 'Meses' }
  ];

  const taskTypes = [
    { value: 'newsletter', label: 'Newsletter (Descoberta + Envio no Email)' },
    { value: 'startup_discovery', label: 'Descoberta de Startups' },
  ];

  // Removidos os arrays de opções - agora tudo será dinâmico

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const data = await jobsService.getJobs();
      setJobs(data);
    } catch (error) {
      console.error('Erro ao carregar jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingJob) {
        await jobsService.updateJob(editingJob.id, formData);
      } else {
        await jobsService.createJob(formData);
      }

      setShowModal(false);
      setEditingJob(null);
      setFormData({
        name: '',
        task_type: 'newsletter',
        interval_value: 1,
        interval_unit: 'hours',
        task_config: {
          country: '',
          sector: '',
          limit: 10
        }
      });
      loadJobs();
    } catch (error) {
      console.error('Erro ao salvar job:', error);
    }
  };

  const handleEdit = (job) => {
    setEditingJob(job);
    setFormData({
      name: job.name,
      task_type: job.task_type,
      interval_value: job.interval_value,
      interval_unit: job.interval_unit,
      task_config: job.task_config || {
        country: '',
        sector: '',
        limit: 10
      }
    });
    setShowModal(true);
  };

  const handleDelete = async (jobId) => {
    if (window.confirm('Tem certeza que deseja remover este job?')) {
      try {
        await jobsService.deleteJob(jobId);
        loadJobs();
      } catch (error) {
        console.error('Erro ao deletar job:', error);
      }
    }
  };

  const handleToggle = async (jobId) => {
    try {
      await jobsService.toggleJob(jobId);
      loadJobs();
    } catch (error) {
      console.error('Erro ao alterar status do job:', error);
    }
  };

  const formatNextRun = (nextRun) => {
    if (!nextRun) return 'Não agendado';
    const date = new Date(nextRun);
    return date.toLocaleString('pt-BR');
  };

  const formatLastRun = (lastRun) => {
    if (!lastRun) return 'Nunca executado';
    const date = new Date(lastRun);
    return date.toLocaleString('pt-BR');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-nvidia-green text-2xl">Carregando configurações...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Configurações</h1>
        <button
          onClick={() => {
            setEditingJob(null);
            setFormData({
              name: '',
              task_type: 'newsletter',
              interval_value: 1,
              interval_unit: 'hours',
              task_config: {
                country: 'Brazil',
                sector: '',
                limit: 10,
                search_strategy: 'specific'
              }
            });
            setShowModal(true);
          }}
          className="bg-nvidia-green text-nvidia-dark px-4 py-2 rounded-md hover:bg-green-600 transition-colors flex items-center space-x-2"
        >
          <ion-icon name="add-outline"></ion-icon>
          <span>Nova Task</span>
        </button>
      </div>

      {/* Tasks Agendadas */}
      <div className="bg-nvidia-gray rounded-lg overflow-hidden mt-8">
        <div className="px-6 py-4 bg-nvidia-lightGray">
          <h2 className="text-xl font-semibold text-white">Tasks Agendadas</h2>
          <p className="text-gray-400 text-sm">Configure tarefas automáticas para descoberta de startups</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-nvidia-lightGray">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Configuração
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Intervalo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Última Execução
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Próxima Execução
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nvidia-lightGray">
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-gray-400">
                    Nenhuma task agendada. Clique em "Nova Task" para criar uma.
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-nvidia-lightGray transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-white font-medium">{job.name}</p>
                        {job.description && (
                          <p className="text-gray-400 text-sm">{job.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-300">
                      <div className="text-sm">
                        <div className="text-white font-medium">
                          {!job.task_config?.country && !job.task_config?.sector
                            ? "Busca Global por Demanda"
                            : !job.task_config?.sector
                            ? "Setores Emergentes"
                            : !job.task_config?.country
                            ? "Global - Setor Específico"
                            : "Busca Específica"
                          }
                        </div>
                        <div className="text-gray-400">
                          {job.task_config?.country || 'Global'}
                          {job.task_config?.sector && ` • ${job.task_config.sector}`}
                          {!job.task_config?.sector && ' • Setores de alta demanda'}
                          • Limite: {job.task_config?.limit || 10}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-300">
                      {job.interval_value} {intervalUnits.find(u => u.value === job.interval_unit)?.label.toLowerCase()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        job.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {job.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm">
                      {formatLastRun(job.last_run)}
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm">
                      {formatNextRun(job.next_run)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleToggle(job.id)}
                          className={`p-1 rounded ${
                            job.is_active
                              ? 'text-yellow-400 hover:text-yellow-300'
                              : 'text-green-400 hover:text-green-300'
                          }`}
                          title={job.is_active ? 'Pausar' : 'Ativar'}
                        >
                          <ion-icon
                            name={job.is_active ? 'pause-outline' : 'play-outline'}
                            size="small"
                          ></ion-icon>
                        </button>
                        <button
                          onClick={() => handleEdit(job)}
                          className="text-blue-400 hover:text-blue-300 p-1 rounded"
                          title="Editar"
                        >
                          <ion-icon name="pencil-outline" size="small"></ion-icon>
                        </button>
                        <button
                          onClick={() => handleDelete(job.id)}
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
      </div>

      {/* Newsletter Emails */}
      <div className="mt-12">
        <NewsletterEmails />
      </div>

      {/* Modal para Criar/Editar Task */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-overlay"
          onClick={() => setShowModal(false)}
        >
          <div
            className="bg-nvidia-gray rounded-lg w-full max-w-2xl h-[90vh] flex flex-col m-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header do Modal */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-nvidia-lightGray">
              <h3 className="text-xl font-semibold text-white">
                {editingJob ? 'Editar Task' : 'Nova Task'}
              </h3>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <ion-icon name="close-outline" class="text-2xl"></ion-icon>
              </button>
            </div>

            {/* Conteúdo Scrollável */}
            <div className="flex-1 overflow-y-auto modal-scroll">
              <form id="task-form" onSubmit={handleSubmit} className="p-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Nome
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                  placeholder="Ex: Descoberta Diária de Startups"
                />
              </div>


              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Tipo de Tarefa
                </label>
                <select
                  value={formData.task_type}
                  onChange={(e) => setFormData({ ...formData, task_type: e.target.value })}
                  className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                >
                  {taskTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Configurações da Task */}
              <div className="border-t border-nvidia-lightGray pt-3">
                <h4 className="text-md font-medium text-white mb-3">Configurações da Busca</h4>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      País/Região (opcional)
                    </label>
                    <input
                      type="text"
                      value={formData.task_config.country}
                      onChange={(e) => setFormData({
                        ...formData,
                        task_config: { ...formData.task_config, country: e.target.value }
                      })}
                      className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                      placeholder="Ex: Brazil, América Latina, Argentina..."
                    />
                    <p className="text-xs text-gray-400 mt-1">Deixe vazio para busca global</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Limite de Startups *
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      required
                      value={formData.task_config.limit}
                      onChange={(e) => setFormData({
                        ...formData,
                        task_config: { ...formData.task_config, limit: parseInt(e.target.value) || 1 }
                      })}
                      className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                    />
                  </div>
                </div>

                <div className="mt-3">
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Setor (opcional)
                  </label>
                  <input
                    type="text"
                    value={formData.task_config.sector}
                    onChange={(e) => setFormData({
                      ...formData,
                      task_config: { ...formData.task_config, sector: e.target.value }
                    })}
                    className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                    placeholder="Ex: FinTech, AI, Agro, Educação..."
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Deixe vazio para descobrir automaticamente os setores de maior demanda
                  </p>
                </div>

                {/* Estratégia Automática - Exibe o que vai acontecer */}
                <div className="bg-nvidia-lightGray p-3 rounded-md mt-3">
                  <h5 className="text-sm font-medium text-nvidia-green mb-2">Estratégia que será aplicada:</h5>
                  <p className="text-sm text-gray-300">
                    {!formData.task_config.country && !formData.task_config.sector
                      ? "Busca global por setores emergentes e de alta demanda no mercado"
                      : !formData.task_config.sector
                      ? "Busca por setores emergentes e de demanda crescente no país/região especificado"
                      : !formData.task_config.country
                      ? "Busca global focada no setor especificado"
                      : "Busca específica por país e setor definidos"
                    }
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Intervalo
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={formData.interval_value}
                    onChange={(e) => setFormData({ ...formData, interval_value: parseInt(e.target.value) })}
                    className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Unidade
                  </label>
                  <select
                    value={formData.interval_unit}
                    onChange={(e) => setFormData({ ...formData, interval_unit: e.target.value })}
                    className="w-full bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
                  >
                    {intervalUnits.map(unit => (
                      <option key={unit.value} value={unit.value}>
                        {unit.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              </form>
            </div>

            {/* Rodapé com Botões */}
            <div className="flex justify-end space-x-3 px-4 py-3 border-t border-nvidia-lightGray bg-nvidia-lightGray rounded-b-lg">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-6 py-2 text-gray-300 hover:text-white transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                form="task-form"
                className="bg-nvidia-green text-nvidia-dark px-6 py-2 rounded-md hover:bg-green-600 transition-colors font-medium"
              >
                {editingJob ? 'Atualizar Task' : 'Criar Task'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Settings;
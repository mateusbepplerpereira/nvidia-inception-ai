import { useState, useEffect } from 'react';
import { logsService } from '../services/api';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

function Logs() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState({
    status: '',
    taskType: ''
  });

  const itemsPerPage = 10;

  const statusColors = {
    started: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800'
  };

  const statusLabels = {
    started: 'Iniciado',
    completed: 'Concluído',
    failed: 'Falhou'
  };

  useEffect(() => {
    loadLogs();
    loadStats();
  }, [currentPage, filters]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const offset = (currentPage - 1) * itemsPerPage;
      const data = await logsService.getLogs(
        itemsPerPage,
        offset,
        filters.status || null,
        filters.taskType || null
      );
      setLogs(data);
    } catch (error) {
      console.error('Erro ao carregar logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await logsService.getLogsStats();
      setStats(data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setCurrentPage(1);
  };

  const resetFilters = () => {
    setFilters({
      status: '',
      taskType: ''
    });
    setCurrentPage(1);
  };

  const handleClearLogs = async (status = null, olderThanDays = null) => {
    const confirmMessage = status
      ? `Tem certeza que deseja remover todos os logs com status "${statusLabels[status]}"?`
      : olderThanDays
      ? `Tem certeza que deseja remover todos os logs mais antigos que ${olderThanDays} dias?`
      : 'Tem certeza que deseja remover TODOS os logs?';

    if (window.confirm(confirmMessage)) {
      try {
        await logsService.clearLogs(status, olderThanDays);
        loadLogs();
        loadStats();
      } catch (error) {
        console.error('Erro ao limpar logs:', error);
      }
    }
  };

  const formatExecutionTime = (time) => {
    if (!time) return '-';
    if (time < 60) return `${time.toFixed(1)}s`;
    return `${(time / 60).toFixed(1)}min`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return format(new Date(dateString), 'dd/MM/yyyy HH:mm:ss', { locale: ptBR });
  };

  // Paginação
  const totalPages = Math.ceil((stats.total_logs || 0) / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;

  if (loading && logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-nvidia-green text-2xl">Carregando logs...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Logs do Sistema</h1>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleClearLogs()}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors flex items-center space-x-2"
          >
            <ion-icon name="trash-outline"></ion-icon>
            <span>Limpar Todos</span>
          </button>
          <button
            onClick={() => { loadLogs(); loadStats(); }}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors flex items-center space-x-2"
          >
            <ion-icon name="refresh-outline"></ion-icon>
            <span>Atualizar</span>
          </button>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-nvidia-gray rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-500 rounded-lg">
              <ion-icon name="document-text-outline" class="text-white text-xl"></ion-icon>
            </div>
            <div className="ml-4">
              <p className="text-gray-400 text-sm">Total de Logs</p>
              <p className="text-white text-lg font-semibold">{stats.total_logs || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-500 rounded-lg">
              <ion-icon name="checkmark-circle-outline" class="text-white text-xl"></ion-icon>
            </div>
            <div className="ml-4">
              <p className="text-gray-400 text-sm">Concluídos</p>
              <p className="text-white text-lg font-semibold">
                {stats.by_status?.completed || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-red-500 rounded-lg">
              <ion-icon name="close-circle-outline" class="text-white text-xl"></ion-icon>
            </div>
            <div className="ml-4">
              <p className="text-gray-400 text-sm">Falharam</p>
              <p className="text-white text-lg font-semibold">
                {stats.by_status?.failed || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-nvidia-green rounded-lg">
              <ion-icon name="time-outline" class="text-white text-xl"></ion-icon>
            </div>
            <div className="ml-4">
              <p className="text-gray-400 text-sm">Tempo Médio</p>
              <p className="text-white text-lg font-semibold">
                {formatExecutionTime(stats.avg_execution_time)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-nvidia-gray rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Filtros</h2>
          <button
            onClick={resetFilters}
            className="text-nvidia-green hover:text-green-400 text-sm"
          >
            Limpar Filtros
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green w-full"
            >
              <option value="">Todos os Status</option>
              <option value="started">Iniciado</option>
              <option value="completed">Concluído</option>
              <option value="failed">Falhou</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Tipo de Tarefa</label>
            <select
              value={filters.taskType}
              onChange={(e) => handleFilterChange('taskType', e.target.value)}
              className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green w-full"
            >
              <option value="">Todos os Tipos</option>
              <option value="startup_discovery">Descoberta de Startups</option>
              <option value="orchestration">Orquestração</option>
            </select>
          </div>

        </div>
      </div>

      {/* Lista de Logs */}
      <div className="bg-nvidia-gray rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-full">
            <thead className="bg-nvidia-lightGray">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-16">
                  Task ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-48">
                  Tarefa
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-24">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-32">
                  Tempo
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-32">
                  Iniciado
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-32">
                  Finalizado
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-64">
                  Mensagem
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nvidia-lightGray">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center text-gray-400">
                    Nenhum log encontrado
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-nvidia-lightGray transition-colors">
                    <td className="px-4 py-4">
                      <span className="text-nvidia-green font-mono text-sm font-bold">
                        #{log.id}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div>
                        <p className="text-white font-medium">{log.task_name}</p>
                        <p className="text-gray-400 text-sm">{log.task_type}</p>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${statusColors[log.status] || 'bg-gray-100 text-gray-800'}`}>
                        {statusLabels[log.status] || log.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-gray-300">
                      {formatExecutionTime(log.execution_time)}
                    </td>
                    <td className="px-4 py-4 text-gray-400 text-sm">
                      {formatDate(log.started_at)}
                    </td>
                    <td className="px-4 py-4 text-gray-400 text-sm">
                      {formatDate(log.completed_at)}
                    </td>
                    <td className="px-4 py-4">
                      <p className="text-gray-300 text-sm">
                        {log.message || '-'}
                      </p>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Paginação */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-gray-400">
            Mostrando {startIndex + 1} a {Math.min(startIndex + itemsPerPage, stats.total_logs || 0)} de {stats.total_logs || 0} resultados
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 rounded-md bg-nvidia-gray text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-nvidia-lightGray"
            >
              <ion-icon name="chevron-back-outline"></ion-icon>
            </button>

            {[...Array(Math.min(5, totalPages))].map((_, idx) => {
              const pageNum = currentPage > 3 ? currentPage - 2 + idx : idx + 1;
              if (pageNum > totalPages) return null;
              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`px-3 py-1 rounded-md ${
                    currentPage === pageNum
                      ? 'bg-nvidia-green text-nvidia-dark'
                      : 'bg-nvidia-gray text-white hover:bg-nvidia-lightGray'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 rounded-md bg-nvidia-gray text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-nvidia-lightGray"
            >
              <ion-icon name="chevron-forward-outline"></ion-icon>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Logs;
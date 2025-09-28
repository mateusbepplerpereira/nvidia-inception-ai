import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { startupService, agentService } from '../services/api';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import ReportModal from '../components/ReportModal';

function Startups() {
  const navigate = useNavigate();
  const [startups, setStartups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState({
    search: '',
    sector: '',
    technology: '',
    country: '',
    sortBy: 'score',
    sortOrder: 'desc'
  });
  const [metricsData, setMetricsData] = useState({});
  const [availableFilters, setAvailableFilters] = useState({
    sectors: [],
    technologies: [],
    countries: []
  });
  const [showReportModal, setShowReportModal] = useState(false);
  // Estados do modal movidos para o componente

  const itemsPerPage = 10;

  useEffect(() => {
    loadStartups();
    loadMetrics();
  }, []);

  // Modal gerenciado pelo componente

  const loadStartups = async () => {
    try {
      setLoading(true);
      const data = await startupService.getStartups({ limit: 1000 });
      setStartups(data);

      // Extract unique values for filters
      const sectors = [...new Set(data.map(s => s.sector).filter(Boolean))];
      const technologies = [...new Set(data.flatMap(s => s.ai_technologies || []))];
      const countries = [...new Set(data.map(s => s.country).filter(Boolean))];

      setAvailableFilters({
        sectors: sectors.sort(),
        technologies: technologies.sort(),
        countries: countries.sort()
      });
    } catch (error) {
      console.error('Error loading startups:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      const rankingData = await agentService.getMetricsRanking();
      const metrics = {};
      rankingData.ranking.forEach(item => {
        metrics[item.startup.id] = item.metrics;
      });
      setMetricsData(metrics);
    } catch (error) {
      console.error('Error loading metrics:', error);
    }
  };

  // Filter and sort startups
  const filteredStartups = startups.filter(startup => {
    if (filters.search && !startup.name.toLowerCase().includes(filters.search.toLowerCase())) return false;
    if (filters.sector && startup.sector !== filters.sector) return false;
    if (filters.technology && !startup.ai_technologies?.includes(filters.technology)) return false;
    if (filters.country && startup.country !== filters.country) return false;
    return true;
  }).sort((a, b) => {
    switch (filters.sortBy) {
      case 'name':
        const nameOrder = filters.sortOrder === 'asc' ? 1 : -1;
        return nameOrder * (a.name || '').localeCompare(b.name || '');
      case 'sector':
        const sectorOrder = filters.sortOrder === 'asc' ? 1 : -1;
        return sectorOrder * (a.sector || '').localeCompare(b.sector || '');
      case 'created_at':
        const dateOrder = filters.sortOrder === 'asc' ? 1 : -1;
        return dateOrder * (new Date(b.created_at) - new Date(a.created_at));
      case 'score':
        const scoreA = metricsData[a.id]?.total_score || a.analysis?.[0]?.priority_score || 0;
        const scoreB = metricsData[b.id]?.total_score || b.analysis?.[0]?.priority_score || 0;
        // Para score: desc = maiores primeiro, asc = menores primeiro
        return filters.sortOrder === 'desc' ? (scoreB - scoreA) : (scoreA - scoreB);
      default:
        return 0;
    }
  });

  // Pagination
  const totalPages = Math.ceil(filteredStartups.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedStartups = filteredStartups.slice(startIndex, startIndex + itemsPerPage);

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setCurrentPage(1);
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      sector: '',
      technology: '',
      country: '',
      sortBy: 'score',
      sortOrder: 'desc'
    });
    setCurrentPage(1);
  };


  // Função movida para o componente

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-nvidia-green text-2xl">Carregando startups...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Startups</h1>
        <div className="flex items-center space-x-4">
          <span className="text-gray-400">Total: {filteredStartups.length} startups</span>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowReportModal(true)}
              className="bg-nvidia-green text-nvidia-dark px-4 py-2 rounded-md hover:bg-green-600 transition-colors flex items-center space-x-2"
            >
              <ion-icon name="document-text-outline"></ion-icon>
              <span>Gerar Relatório</span>
            </button>
            <button
              onClick={() => { loadStartups(); loadMetrics(); }}
              className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors flex items-center space-x-2"
            >
              <ion-icon name="refresh-outline"></ion-icon>
              <span>Atualizar</span>
            </button>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-nvidia-gray rounded-lg p-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Pesquisar por nome da startup..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            className="w-full bg-nvidia-lightGray text-white rounded-md px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
          />
          <ion-icon
            name="search-outline"
            class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl"
          ></ion-icon>
        </div>
      </div>

      {/* Filters */}
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

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Setor</label>
            <select
              value={filters.sector}
              onChange={(e) => handleFilterChange('sector', e.target.value)}
              className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green w-full"
            >
              <option value="">Todos os Setores</option>
              {availableFilters.sectors.map(sector => (
                <option key={sector} value={sector}>{sector}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Tecnologia</label>
            <select
              value={filters.technology}
              onChange={(e) => handleFilterChange('technology', e.target.value)}
              className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green w-full"
            >
              <option value="">Todas as Tecnologias</option>
              {availableFilters.technologies.map(tech => (
                <option key={tech} value={tech}>{tech}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">País</label>
            <select
              value={filters.country}
              onChange={(e) => handleFilterChange('country', e.target.value)}
              className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green w-full"
            >
              <option value="">Todos os Países</option>
              {availableFilters.countries.map(country => (
                <option key={country} value={country}>{country}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Ordenar por</label>
            <select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
              className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green w-full"
            >
              <option value="created_at">Data de Adição</option>
              <option value="name">Nome</option>
              <option value="sector">Setor</option>
              <option value="score">Potencial Parceria</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Ordem</label>
            <select
              value={filters.sortOrder}
              onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
              className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green w-full"
            >
              <option value="desc">Decrescente</option>
              <option value="asc">Crescente</option>
            </select>
          </div>
        </div>
      </div>

      {/* Startups List */}
      <div className="bg-nvidia-gray rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-full">
            <thead className="bg-nvidia-lightGray">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-48">
                  Startup
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-24">
                  Setor
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-32">
                  Tecnologias
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-24">
                  País
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-20">
                  Score
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-24">
                  Adicionada
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-20">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nvidia-lightGray">
              {paginatedStartups.map((startup) => (
                <tr key={startup.id} className="hover:bg-nvidia-lightGray transition-colors">
                  <td className="px-4 py-4 whitespace-nowrap">
                    <div>
                      <p className="text-white font-medium">{startup.name}</p>
                      {startup.city && (
                        <p className="text-gray-400 text-sm">{startup.city}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-gray-300">
                    <span className="hidden md:inline">{startup.sector || '-'}</span>
                    <span className="md:hidden">
                      {startup.sector ? startup.sector.substring(0, 10) + (startup.sector.length > 10 ? '...' : '') : '-'}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-wrap gap-1">
                      {startup.ai_technologies?.slice(0, 2).map((tech, idx) => (
                        <span key={idx} className="px-2 py-1 text-xs bg-nvidia-green text-nvidia-dark rounded">
                          {tech}
                        </span>
                      ))}
                      {startup.ai_technologies?.length > 2 && (
                        <span className="px-2 py-1 text-xs bg-nvidia-lightGray text-gray-300 rounded">
                          +{startup.ai_technologies.length - 2}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-gray-300">
                    {startup.country || '-'}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    {metricsData[startup.id]?.total_score ? (
                      <span className="text-nvidia-green font-semibold">
                        {metricsData[startup.id].total_score.toFixed(1)}
                      </span>
                    ) : startup.analysis?.[0]?.priority_score ? (
                      <span className="text-nvidia-green font-semibold">
                        {startup.analysis[0].priority_score.toFixed(1)}
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-gray-400 text-sm">
                    <span className="hidden md:inline">
                      {format(new Date(startup.created_at), 'dd MMM yyyy', { locale: ptBR })}
                    </span>
                    <span className="md:hidden">
                      {format(new Date(startup.created_at), 'dd/MM', { locale: ptBR })}
                    </span>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <button
                      onClick={() => navigate(`/startups/${startup.id}`)}
                      className="text-nvidia-green hover:text-green-400"
                    >
                      <ion-icon name="eye-outline" size="large"></ion-icon>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-gray-400">
            Mostrando {startIndex + 1} a {Math.min(startIndex + itemsPerPage, filteredStartups.length)} de {filteredStartups.length} resultados
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

      {/* Report Modal */}
      <ReportModal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        availableMetrics={availableFilters}
        title="Gerar Relatório de Startups"
      />
    </div>
  );
}

export default Startups;
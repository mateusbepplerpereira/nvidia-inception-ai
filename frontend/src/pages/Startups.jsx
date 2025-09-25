import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { startupService } from '../services/api';
import { format } from 'date-fns';

function Startups() {
  const navigate = useNavigate();
  const [startups, setStartups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState({
    sector: '',
    technology: '',
    country: '',
    hasVC: '',
    sortBy: 'created_at',
    sortOrder: 'desc'
  });
  const [availableFilters, setAvailableFilters] = useState({
    sectors: [],
    technologies: [],
    countries: []
  });

  const itemsPerPage = 10;

  useEffect(() => {
    loadStartups();
  }, []);

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

  // Filter and sort startups
  const filteredStartups = startups.filter(startup => {
    if (filters.sector && startup.sector !== filters.sector) return false;
    if (filters.technology && !startup.ai_technologies?.includes(filters.technology)) return false;
    if (filters.country && startup.country !== filters.country) return false;
    if (filters.hasVC !== '' && startup.has_venture_capital !== (filters.hasVC === 'true')) return false;
    return true;
  }).sort((a, b) => {
    const order = filters.sortOrder === 'asc' ? 1 : -1;
    switch (filters.sortBy) {
      case 'name':
        return order * (a.name || '').localeCompare(b.name || '');
      case 'sector':
        return order * (a.sector || '').localeCompare(b.sector || '');
      case 'created_at':
        return order * (new Date(b.created_at) - new Date(a.created_at));
      case 'score':
        const scoreA = a.analysis?.[0]?.priority_score || 0;
        const scoreB = b.analysis?.[0]?.priority_score || 0;
        return order * (scoreB - scoreA);
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
      sector: '',
      technology: '',
      country: '',
      hasVC: '',
      sortBy: 'created_at',
      sortOrder: 'desc'
    });
    setCurrentPage(1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-nvidia-green text-2xl">Loading startups...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Startups</h1>
        <div className="flex items-center space-x-4">
          <span className="text-gray-400">Total: {filteredStartups.length} startups</span>
          <button
            onClick={loadStartups}
            className="bg-nvidia-green text-nvidia-dark px-4 py-2 rounded-md hover:bg-green-600 transition-colors flex items-center space-x-2"
          >
            <ion-icon name="refresh-outline"></ion-icon>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-nvidia-gray rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Filters</h2>
          <button
            onClick={resetFilters}
            className="text-nvidia-green hover:text-green-400 text-sm"
          >
            Reset Filters
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <select
            value={filters.sector}
            onChange={(e) => handleFilterChange('sector', e.target.value)}
            className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
          >
            <option value="">All Sectors</option>
            {availableFilters.sectors.map(sector => (
              <option key={sector} value={sector}>{sector}</option>
            ))}
          </select>

          <select
            value={filters.technology}
            onChange={(e) => handleFilterChange('technology', e.target.value)}
            className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
          >
            <option value="">All Technologies</option>
            {availableFilters.technologies.map(tech => (
              <option key={tech} value={tech}>{tech}</option>
            ))}
          </select>

          <select
            value={filters.country}
            onChange={(e) => handleFilterChange('country', e.target.value)}
            className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
          >
            <option value="">All Countries</option>
            {availableFilters.countries.map(country => (
              <option key={country} value={country}>{country}</option>
            ))}
          </select>

          <select
            value={filters.hasVC}
            onChange={(e) => handleFilterChange('hasVC', e.target.value)}
            className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
          >
            <option value="">VC Status</option>
            <option value="true">With VC</option>
            <option value="false">No VC</option>
          </select>

          <select
            value={filters.sortBy}
            onChange={(e) => handleFilterChange('sortBy', e.target.value)}
            className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
          >
            <option value="created_at">Date Added</option>
            <option value="name">Name</option>
            <option value="sector">Sector</option>
            <option value="score">Priority Score</option>
          </select>

          <select
            value={filters.sortOrder}
            onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
            className="bg-nvidia-lightGray text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>

      {/* Startups List */}
      <div className="bg-nvidia-gray rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-nvidia-lightGray">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Startup
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Sector
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Technologies
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Country
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                VC Funding
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Score
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Added
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-nvidia-lightGray">
            {paginatedStartups.map((startup) => (
              <tr key={startup.id} className="hover:bg-nvidia-lightGray transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <p className="text-white font-medium">{startup.name}</p>
                    {startup.city && (
                      <p className="text-gray-400 text-sm">{startup.city}</p>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                  {startup.sector || '-'}
                </td>
                <td className="px-6 py-4">
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
                <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                  {startup.country || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {startup.has_venture_capital ? (
                    <span className="text-nvidia-green">
                      <ion-icon name="checkmark-circle"></ion-icon>
                    </span>
                  ) : (
                    <span className="text-gray-500">
                      <ion-icon name="close-circle"></ion-icon>
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {startup.analysis?.[0]?.priority_score ? (
                    <span className="text-nvidia-green font-semibold">
                      {startup.analysis[0].priority_score.toFixed(1)}
                    </span>
                  ) : (
                    <span className="text-gray-500">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-400 text-sm">
                  {format(new Date(startup.created_at), 'MMM dd, yyyy')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
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

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-gray-400">
            Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredStartups.length)} of {filteredStartups.length} results
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

export default Startups;
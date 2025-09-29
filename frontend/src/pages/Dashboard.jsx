import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { startupService, agentService } from '../services/api';
import ReportModal from '../components/ReportModal';

function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalStartups: 0,
    topStartup: null,
    mostUsedTech: 'N/A',
    topSector: 'N/A',
    topTechnologies: [],
    countryDistribution: [],
    sectorDistribution: [],
    topStartups: [],
    highestScore: 0,
    lowestScore: 0
  });

  // Custom tooltip component for pie charts
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: '#2D2D2D',
          border: 'none',
          padding: '8px 12px',
          borderRadius: '4px',
          color: 'white',
          fontSize: '14px'
        }}>
          <p style={{ color: 'white', margin: 0 }}>
            {`${payload[0].name}: ${payload[0].value}`}
          </p>
        </div>
      );
    }
    return null;
  };
  const [loading, setLoading] = useState(true);
  const [showReportModal, setShowReportModal] = useState(false);
  const [availableFilters, setAvailableFilters] = useState({
    sectors: [],
    technologies: [],
    countries: []
  });
  // Modal gerenciado pelo componente

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Modal gerenciado pelo componente ReportModal

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      // Get startups data and ranking in parallel
      const [startups, rankingData] = await Promise.all([
        startupService.getStartups({ limit: 1000 }),
        agentService.getMetricsRanking()
      ]);

      // Process data for dashboard
      const totalStartups = startups.length;

      // Calculate average scores
      // Use ranking data for top startups
      const rankedStartups = rankingData.ranking || [];

      // Get sector distribution
      const sectorCounts = {};
      startups.forEach(s => {
        if (s.sector) {
          sectorCounts[s.sector] = (sectorCounts[s.sector] || 0) + 1;
        }
      });

      const sectorDistribution = Object.entries(sectorCounts)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value);

      // Get technology distribution
      const techCounts = {};
      startups.forEach(s => {
        if (s.ai_technologies) {
          s.ai_technologies.forEach(tech => {
            techCounts[tech] = (techCounts[tech] || 0) + 1;
          });
        }
      });

      const topTechnologies = Object.entries(techCounts)
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 8);

      // Get country distribution
      const countryCounts = {};
      startups.forEach(s => {
        if (s.country) {
          countryCounts[s.country] = (countryCounts[s.country] || 0) + 1;
        }
      });

      const countryDistribution = Object.entries(countryCounts)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 6);

      // Get top 5 startups from ranking API
      const topStartups = rankedStartups.slice(0, 5).map(item => ({
        id: item.startup.id,
        name: item.startup.name,
        sector: item.startup.sector,
        totalScore: item.metrics.total_score,
        techScore: item.metrics.technical_level_score,
        marketScore: item.metrics.market_demand_score,
        partnershipScore: item.metrics.partnership_potential_score,
        fundingAmount: item.startup.last_funding_amount || 0,
        rank: item.rank
      }));

      // Get top startup from ranking
      const topStartup = topStartups[0] || null;

      // Get most used technology
      const mostUsedTech = topTechnologies[0]?.name || 'N/A';

      // Get top sector
      const topSector = sectorDistribution[0]?.name || 'N/A';

      // Extract unique values for filters
      const sectors = [...new Set(startups.map(s => s.sector).filter(Boolean))];
      const technologies = [...new Set(startups.flatMap(s => s.ai_technologies || []))];
      const countries = [...new Set(startups.map(s => s.country).filter(Boolean))];

      setAvailableFilters({
        sectors: sectors.sort(),
        technologies: technologies.sort(),
        countries: countries.sort()
      });

      setStats({
        totalStartups,
        topStartup,
        mostUsedTech,
        topSector,
        topTechnologies,
        countryDistribution,
        sectorDistribution,
        topStartups,
        highestScore: rankingData.highest_score || 0,
        lowestScore: rankingData.lowest_score || 0,
        totalAnalyzed: rankingData.total_analyzed || 0
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };


  const COLORS = ['#76B900', '#4CAF50', '#8BC34A', '#CDDC39', '#FFC107'];


  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-nvidia-green text-2xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowReportModal(true)}
            className="bg-nvidia-green text-nvidia-dark px-4 py-2 rounded-md hover:bg-green-600 transition-colors flex items-center space-x-2"
          >
            <ion-icon name="document-text-outline"></ion-icon>
            <span>Gerar Relatório</span>
          </button>
          <button
            onClick={loadDashboardData}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors flex items-center space-x-2"
          >
            <ion-icon name="refresh-outline"></ion-icon>
            <span>Atualizar</span>
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-nvidia-gray rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total de Startups</p>
              <p className="text-3xl font-bold text-white mt-1">{stats.totalStartups}</p>
            </div>
            <ion-icon name="business" class="text-nvidia-green text-4xl"></ion-icon>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Tecnologia Mais Usada</p>
              <p className="text-2xl font-bold text-white mt-1">{stats.mostUsedTech}</p>
            </div>
            <ion-icon name="code-slash-outline" class="text-nvidia-green text-4xl"></ion-icon>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Setor Principal</p>
              <p className="text-2xl font-bold text-white mt-1">{stats.topSector}</p>
            </div>
            <ion-icon name="business-outline" class="text-nvidia-green text-4xl"></ion-icon>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Top Startup</p>
              <p className="text-xl font-bold text-white mt-1">{stats.topStartup?.name || 'N/A'}</p>
              <p className="text-nvidia-green text-lg font-semibold">Score: {stats.topStartup?.totalScore?.toFixed(1) || 0}</p>
            </div>
            <ion-icon name="trophy-outline" class="text-nvidia-green text-4xl"></ion-icon>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Country Distribution */}
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Startups por País</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats.countryDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {stats.countryDistribution.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Sector Distribution */}
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Startups por Setor</h2>
          <div className="w-full h-80 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={stats.sectorDistribution}
                margin={{ top: 20, right: 20, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#4A4A4A" />
                <XAxis
                  type="number"
                  stroke="#999"
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#999"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(value) => value.length > 15 ? `${value.substring(0, 15)}...` : value}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#2D2D2D',
                    border: 'none',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                />
                <Bar dataKey="value" fill="#76B900">
                  {stats.sectorDistribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Technologies - Full Width */}
        <div className="bg-nvidia-gray rounded-lg p-6 md:col-span-2">
          <h2 className="text-xl font-semibold text-white mb-4">Tecnologias Mais Utilizadas</h2>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={stats.topTechnologies} margin={{ bottom: 120 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#4A4A4A" />
              <XAxis
                dataKey="name"
                stroke="#999"
                angle={-45}
                textAnchor="end"
                interval={0}
                height={100}
                tick={{ fontSize: 12 }}
              />
              <YAxis stroke="#999" />
              <Tooltip contentStyle={{ backgroundColor: '#2D2D2D', border: 'none' }} />
              <Bar dataKey="count" fill="#76B900">
                {stats.topTechnologies.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Startups with Metrics */}
        <div className="bg-nvidia-gray rounded-lg p-6 md:col-span-2">
          <h2 className="text-xl font-semibold text-white mb-4">Top Startups com Maior Potencial</h2>
          <div className="space-y-3">
            {stats.topStartups.length > 0 ? stats.topStartups.map((startup) => (
              <div
                key={startup.id}
                className="flex items-center justify-between p-4 bg-nvidia-lightGray rounded-lg cursor-pointer hover:bg-nvidia-gray transition-colors"
                onClick={() => navigate(`/startups/${startup.id}`)}
              >
                <div className="flex items-center space-x-4">
                  <span className="text-nvidia-green font-bold text-2xl">#{startup.rank}</span>
                  <div className="flex-1">
                    <p className="text-white font-semibold text-lg">{startup.name}</p>
                    <p className="text-gray-400">{startup.sector}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-nvidia-green font-bold text-2xl">{startup.totalScore?.toFixed(1) || 0}</p>
                  <p className="text-gray-400 text-sm">Score Total</p>
                </div>
              </div>
            )) : (
              <div className="text-center py-8 text-gray-400">
                <p>Nenhuma startup com métricas disponível</p>
              </div>
            )}
          </div>
        </div>
      </div>

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

export default Dashboard;
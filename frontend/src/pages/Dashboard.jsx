import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { startupService } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState({
    totalStartups: 0,
    withVenture: 0,
    avgScore: 0,
    topSectors: [],
    topTechnologies: [],
    monthlyGrowth: [],
    sectorDistribution: [],
    topStartups: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const startups = await startupService.getStartups({ limit: 1000 });

      // Process data for dashboard
      const totalStartups = startups.length;
      const withVenture = startups.filter(s => s.has_venture_capital).length;

      // Calculate average scores
      const startupsWithScores = startups.filter(s => s.analysis?.length > 0);
      const avgScore = startupsWithScores.length > 0
        ? startupsWithScores.reduce((acc, s) => acc + (s.analysis[0]?.priority_score || 0), 0) / startupsWithScores.length
        : 0;

      // Get sector distribution
      const sectorCounts = {};
      startups.forEach(s => {
        if (s.sector) {
          sectorCounts[s.sector] = (sectorCounts[s.sector] || 0) + 1;
        }
      });

      const sectorDistribution = Object.entries(sectorCounts)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 5);

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

      // Get monthly growth (simulated)
      const monthlyGrowth = [
        { month: 'Jan', count: 12 },
        { month: 'Feb', count: 18 },
        { month: 'Mar', count: 25 },
        { month: 'Apr', count: 32 },
        { month: 'May', count: 45 },
        { month: 'Jun', count: 58 }
      ];

      // Get top startups by score
      const topStartups = startupsWithScores
        .sort((a, b) => (b.analysis[0]?.priority_score || 0) - (a.analysis[0]?.priority_score || 0))
        .slice(0, 5)
        .map(s => ({
          id: s.id,
          name: s.name,
          sector: s.sector,
          score: s.analysis[0]?.priority_score || 0,
          technologies: s.ai_technologies || []
        }));

      setStats({
        totalStartups,
        withVenture,
        avgScore: avgScore.toFixed(1),
        topSectors: sectorDistribution,
        topTechnologies,
        monthlyGrowth,
        sectorDistribution,
        topStartups
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
        <button
          onClick={loadDashboardData}
          className="bg-nvidia-green text-nvidia-dark px-4 py-2 rounded-md hover:bg-green-600 transition-colors flex items-center space-x-2"
        >
          <ion-icon name="refresh-outline"></ion-icon>
          <span>Refresh</span>
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-nvidia-gray rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Startups</p>
              <p className="text-3xl font-bold text-white mt-1">{stats.totalStartups}</p>
            </div>
            <ion-icon name="business" class="text-nvidia-green text-4xl"></ion-icon>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">With VC Funding</p>
              <p className="text-3xl font-bold text-white mt-1">{stats.withVenture}</p>
            </div>
            <ion-icon name="cash-outline" class="text-nvidia-green text-4xl"></ion-icon>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Avg Priority Score</p>
              <p className="text-3xl font-bold text-white mt-1">{stats.avgScore}</p>
            </div>
            <ion-icon name="trending-up-outline" class="text-nvidia-green text-4xl"></ion-icon>
          </div>
        </div>

        <div className="bg-nvidia-gray rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Success Rate</p>
              <p className="text-3xl font-bold text-white mt-1">
                {stats.totalStartups > 0 ? ((stats.withVenture / stats.totalStartups) * 100).toFixed(0) : 0}%
              </p>
            </div>
            <ion-icon name="checkmark-circle-outline" class="text-nvidia-green text-4xl"></ion-icon>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Monthly Growth */}
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Monthly Growth</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.monthlyGrowth}>
              <CartesianGrid strokeDasharray="3 3" stroke="#4A4A4A" />
              <XAxis dataKey="month" stroke="#999" />
              <YAxis stroke="#999" />
              <Tooltip contentStyle={{ backgroundColor: '#2D2D2D', border: 'none' }} />
              <Line type="monotone" dataKey="count" stroke="#76B900" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Sector Distribution */}
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Startups by Sector</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats.sectorDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {stats.sectorDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#2D2D2D', border: 'none' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Technologies */}
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Most Used AI Technologies</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.topTechnologies} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" stroke="#4A4A4A" />
              <XAxis type="number" stroke="#999" />
              <YAxis dataKey="name" type="category" stroke="#999" width={100} />
              <Tooltip contentStyle={{ backgroundColor: '#2D2D2D', border: 'none' }} />
              <Bar dataKey="count" fill="#76B900" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Startups */}
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Top Startups with Highest Potential</h2>
          <div className="space-y-3">
            {stats.topStartups.map((startup, index) => (
              <div key={startup.id} className="flex items-center justify-between p-3 bg-nvidia-lightGray rounded-lg">
                <div className="flex items-center space-x-3">
                  <span className="text-nvidia-green font-bold text-lg">#{index + 1}</span>
                  <div>
                    <p className="text-white font-medium">{startup.name}</p>
                    <p className="text-gray-400 text-sm">{startup.sector}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-nvidia-green font-bold text-lg">{startup.score.toFixed(1)}</p>
                  <p className="text-gray-400 text-sm">Score</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
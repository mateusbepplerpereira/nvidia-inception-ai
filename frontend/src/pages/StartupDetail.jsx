import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { startupService, agentService } from '../services/api';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

function StartupDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [startup, setStartup] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStartup();
    loadMetrics();
  }, [id]);

  const loadStartup = async () => {
    try {
      const data = await startupService.getStartup(id);
      setStartup(data);
    } catch (error) {
      console.error('Error loading startup:', error);
      navigate('/startups');
    }
  };

  const loadMetrics = async () => {
    try {
      const rankingData = await agentService.getMetricsRanking();
      const startupMetrics = rankingData.ranking.find(item => item.startup.id === parseInt(id));
      if (startupMetrics) {
        setMetrics(startupMetrics.metrics);
      }
    } catch (error) {
      console.error('Error loading metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-nvidia-green text-2xl">Carregando detalhes da startup...</div>
      </div>
    );
  }

  if (!startup) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-red-500 text-2xl">Startup não encontrada</div>
      </div>
    );
  }

  const analysis = startup.analysis?.[0];

  // Prepare radar chart data
  const radarData = metrics ? [
    {
      metric: 'Demanda de Mercado',
      value: metrics.market_demand_score || 0,
      fullMark: 100
    },
    {
      metric: 'Nível Técnico',
      value: metrics.technical_level_score || 0,
      fullMark: 100
    },
    {
      metric: 'Potencial de Parceria',
      value: metrics.partnership_potential_score || 0,
      fullMark: 100
    }
  ] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/startups')}
          className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
        >
          <ion-icon name="arrow-back-outline" size="large"></ion-icon>
          <span>Voltar para Startups</span>
        </button>
      </div>

      {/* Main Info */}
      <div className="bg-nvidia-gray rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{startup.name}</h1>
            <div className="flex items-center space-x-4 text-gray-400">
              {startup.sector && (
                <div className="flex items-center space-x-1">
                  <ion-icon name="business-outline"></ion-icon>
                  <span>{startup.sector}</span>
                </div>
              )}
              {startup.country && (
                <div className="flex items-center space-x-1">
                  <ion-icon name="location-outline"></ion-icon>
                  <span>{startup.city ? `${startup.city}, ` : ''}{startup.country}</span>
                </div>
              )}
              {startup.founded_year && (
                <div className="flex items-center space-x-1">
                  <ion-icon name="calendar-outline"></ion-icon>
                  <span>Fundada em {startup.founded_year}</span>
                </div>
              )}
            </div>
          </div>
          {startup.website && (
            <a
              href={startup.website}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-nvidia-green text-nvidia-dark px-4 py-2 rounded-md hover:bg-green-600 transition-colors flex items-center space-x-2"
            >
              <ion-icon name="globe-outline"></ion-icon>
              <span>Visitar Website</span>
            </a>
          )}
        </div>

        {startup.description && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-white mb-2">Descrição</h3>
            <p className="text-gray-300">{startup.description}</p>
          </div>
        )}
      </div>

      {/* Technologies */}
      <div className="bg-nvidia-gray rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Tecnologias de IA</h2>
        <div className="flex flex-wrap gap-2">
          {startup.ai_technologies?.map((tech, idx) => (
            <span key={idx} className="px-3 py-2 bg-nvidia-green text-nvidia-dark rounded-md font-medium">
              {tech}
            </span>
          )) || <span className="text-gray-400">Nenhuma tecnologia listada</span>}
        </div>
      </div>

      {/* Metrics Radar Chart */}
      {metrics && (
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-6">Análise de Métricas NVIDIA</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="flex justify-center">
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#4A4A4A" />
                  <PolarAngleAxis dataKey="metric" stroke="#999" className="text-sm" />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    stroke="#999"
                    className="text-xs"
                  />
                  <Radar
                    name="Score"
                    dataKey="value"
                    stroke="#76B900"
                    fill="#76B900"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">Demanda de Mercado</span>
                  <span className="text-nvidia-green font-bold">{metrics.market_demand_score?.toFixed(1) || 0}/100</span>
                </div>
                <div className="w-full bg-nvidia-lightGray rounded-full h-3">
                  <div
                    className="bg-nvidia-green h-3 rounded-full"
                    style={{ width: `${metrics.market_demand_score || 0}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">Nível Técnico</span>
                  <span className="text-blue-400 font-bold">{metrics.technical_level_score?.toFixed(1) || 0}/100</span>
                </div>
                <div className="w-full bg-nvidia-lightGray rounded-full h-3">
                  <div
                    className="bg-blue-500 h-3 rounded-full"
                    style={{ width: `${metrics.technical_level_score || 0}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">Potencial de Parceria</span>
                  <span className="text-purple-400 font-bold">{metrics.partnership_potential_score?.toFixed(1) || 0}/100</span>
                </div>
                <div className="w-full bg-nvidia-lightGray rounded-full h-3">
                  <div
                    className="bg-purple-500 h-3 rounded-full"
                    style={{ width: `${metrics.partnership_potential_score || 0}%` }}
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-nvidia-lightGray">
                <div className="flex justify-between">
                  <span className="text-white font-semibold text-lg">Score Total</span>
                  <span className="text-nvidia-green font-bold text-2xl">{metrics.total_score?.toFixed(1) || 0}/100</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Metrics Explanation Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Market Demand Card */}
          <div className="bg-nvidia-gray rounded-lg p-6 border-l-4 border-nvidia-green">
            <div className="flex items-center mb-3">
              <ion-icon name="trending-up-outline" class="text-nvidia-green text-2xl mr-2"></ion-icon>
              <h3 className="text-lg font-semibold text-white">Demanda de Mercado</h3>
            </div>
            <div className="text-sm text-gray-300 space-y-2">
              <p><strong>Como é calculada:</strong></p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Computer Vision: 85-95 pontos</li>
                <li>NLP: 80-90 pontos</li>
                <li>Machine Learning: 70-85 pontos</li>
                <li>GPU-relevante (Deep Learning, Computer Vision): +20 pontos</li>
                <li>B2B enterprise: +15 pontos</li>
              </ul>
              <p className="text-nvidia-green font-medium mt-2">
                Score atual: {metrics.market_demand_score?.toFixed(1) || 0}/100
              </p>
            </div>
          </div>

          {/* Technical Level Card */}
          <div className="bg-nvidia-gray rounded-lg p-6 border-l-4 border-blue-500">
            <div className="flex items-center mb-3">
              <ion-icon name="code-outline" class="text-blue-400 text-2xl mr-2"></ion-icon>
              <h3 className="text-lg font-semibold text-white">Nível Técnico</h3>
            </div>
            <div className="text-sm text-gray-300 space-y-2">
              <p><strong>Como é calculada:</strong></p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Deep Learning: 80-100 pontos</li>
                <li>Computer Vision: 70-90 pontos</li>
                <li>Machine Learning: 60-80 pontos</li>
                <li>Multi-modal AI: 90-100 pontos</li>
                <li>Tecnologia única: 60-80 pontos</li>
              </ul>
              <p className="text-blue-400 font-medium mt-2">
                Score atual: {metrics.technical_level_score?.toFixed(1) || 0}/100
              </p>
            </div>
          </div>

          {/* Partnership Potential Card */}
          <div className="bg-nvidia-gray rounded-lg p-6 border-l-4 border-purple-500">
            <div className="flex items-center mb-3">
              <ion-icon name="people-outline" class="text-purple-400 text-2xl mr-2"></ion-icon>
              <h3 className="text-lg font-semibold text-white">Potencial de Parceria</h3>
            </div>
            <div className="text-sm text-gray-300 space-y-2">
              <p><strong>Como é calculada:</strong></p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Funding >$10M: 80-100 pontos</li>
                <li>Funding $1-10M: 60-80 pontos</li>
                <li>Funding &lt;$1M: 30-60 pontos</li>
                <li>Investidores conhecidos: +20 pontos</li>
                <li>Setor AI/GPU intensivo: +15 pontos</li>
              </ul>
              <p className="text-purple-400 font-medium mt-2">
                Score atual: {metrics.partnership_potential_score?.toFixed(1) || 0}/100
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Scores */}
      {analysis && (
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Scores de Análise</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-gray-400">Score de Prioridade</span>
                <span className="text-nvidia-green font-bold">{analysis.priority_score?.toFixed(1) || 0}/100</span>
              </div>
              <div className="w-full bg-nvidia-lightGray rounded-full h-2">
                <div
                  className="bg-nvidia-green h-2 rounded-full"
                  style={{ width: `${analysis.priority_score || 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-gray-400">Score de Tecnologia</span>
                <span className="text-white font-bold">{analysis.technology_score?.toFixed(1) || 0}/100</span>
              </div>
              <div className="w-full bg-nvidia-lightGray rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${analysis.technology_score || 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-gray-400">Oportunidade de Mercado</span>
                <span className="text-white font-bold">{analysis.market_opportunity_score?.toFixed(1) || 0}/100</span>
              </div>
              <div className="w-full bg-nvidia-lightGray rounded-full h-2">
                <div
                  className="bg-yellow-500 h-2 rounded-full"
                  style={{ width: `${analysis.market_opportunity_score || 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-gray-400">Score da Equipe</span>
                <span className="text-white font-bold">{analysis.team_score?.toFixed(1) || 0}/100</span>
              </div>
              <div className="w-full bg-nvidia-lightGray rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full"
                  style={{ width: `${analysis.team_score || 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendation */}
      {analysis?.recommendation && (
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Recomendação da IA</h2>
          <p className="text-gray-300">{analysis.recommendation}</p>
        </div>
      )}

      {/* Additional Information */}
      <div className="bg-nvidia-gray rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Informações Adicionais</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex justify-between">
            <span className="text-gray-400">Adicionada ao Banco de Dados</span>
            <span className="text-white">{format(new Date(startup.created_at), 'dd MMM yyyy HH:mm', { locale: ptBR })}</span>
          </div>
          {startup.updated_at && (
            <div className="flex justify-between">
              <span className="text-gray-400">Última Atualização</span>
              <span className="text-white">{format(new Date(startup.updated_at), 'dd MMM yyyy HH:mm', { locale: ptBR })}</span>
            </div>
          )}
          {analysis?.analysis_date && (
            <div className="flex justify-between">
              <span className="text-gray-400">Data da Análise</span>
              <span className="text-white">{format(new Date(analysis.analysis_date), 'dd MMM yyyy', { locale: ptBR })}</span>
            </div>
          )}
          {metrics?.analysis_date && (
            <div className="flex justify-between">
              <span className="text-gray-400">Data das Métricas</span>
              <span className="text-white">{format(new Date(metrics.analysis_date), 'dd MMM yyyy', { locale: ptBR })}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default StartupDetail;
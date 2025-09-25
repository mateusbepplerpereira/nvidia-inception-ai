import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { startupService } from '../services/api';
import { format } from 'date-fns';

function StartupDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [startup, setStartup] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStartup();
  }, [id]);

  const loadStartup = async () => {
    try {
      setLoading(true);
      const data = await startupService.getStartup(id);
      setStartup(data);
    } catch (error) {
      console.error('Error loading startup:', error);
      navigate('/startups');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-nvidia-green text-2xl">Loading startup details...</div>
      </div>
    );
  }

  if (!startup) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-red-500 text-2xl">Startup not found</div>
      </div>
    );
  }

  const analysis = startup.analysis?.[0];
  const metrics = startup.metrics?.[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/startups')}
          className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
        >
          <ion-icon name="arrow-back-outline" size="large"></ion-icon>
          <span>Back to Startups</span>
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
                  <span>Founded {startup.founded_year}</span>
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
              <span>Visit Website</span>
            </a>
          )}
        </div>

        {startup.description && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-white mb-2">Description</h3>
            <p className="text-gray-300">{startup.description}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Technologies */}
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">AI Technologies</h2>
          <div className="flex flex-wrap gap-2">
            {startup.ai_technologies?.map((tech, idx) => (
              <span key={idx} className="px-3 py-2 bg-nvidia-green text-nvidia-dark rounded-md font-medium">
                {tech}
              </span>
            )) || <span className="text-gray-400">No technologies listed</span>}
          </div>
        </div>

        {/* Funding */}
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Funding Information</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">VC Funding</span>
              <span className="text-white">
                {startup.has_venture_capital ? (
                  <span className="text-nvidia-green">Yes</span>
                ) : (
                  <span className="text-gray-500">No</span>
                )}
              </span>
            </div>
            {startup.total_funding && (
              <div className="flex justify-between">
                <span className="text-gray-400">Total Funding</span>
                <span className="text-white">${(startup.total_funding / 1000000).toFixed(1)}M</span>
              </div>
            )}
            {startup.last_funding_amount && (
              <div className="flex justify-between">
                <span className="text-gray-400">Last Funding</span>
                <span className="text-white">${(startup.last_funding_amount / 1000000).toFixed(1)}M</span>
              </div>
            )}
            {startup.last_funding_date && (
              <div className="flex justify-between">
                <span className="text-gray-400">Last Funding Date</span>
                <span className="text-white">{format(new Date(startup.last_funding_date), 'MMM dd, yyyy')}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Investors */}
      {startup.investor_names && startup.investor_names.length > 0 && (
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Investors</h2>
          <div className="flex flex-wrap gap-2">
            {startup.investor_names.map((investor, idx) => (
              <span key={idx} className="px-3 py-2 bg-nvidia-lightGray text-gray-300 rounded-md">
                {investor}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Analysis & Metrics */}
      {(analysis || metrics) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Analysis Scores */}
          {analysis && (
            <div className="bg-nvidia-gray rounded-lg p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Analysis Scores</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">Priority Score</span>
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
                    <span className="text-gray-400">Technology Score</span>
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
                    <span className="text-gray-400">Market Opportunity</span>
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
                    <span className="text-gray-400">Team Score</span>
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

          {/* Metrics */}
          {metrics && (
            <div className="bg-nvidia-gray rounded-lg p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Partnership Metrics</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">Market Demand</span>
                    <span className="text-nvidia-green font-bold">{metrics.market_demand_score?.toFixed(1) || 0}/100</span>
                  </div>
                  <div className="w-full bg-nvidia-lightGray rounded-full h-2">
                    <div
                      className="bg-nvidia-green h-2 rounded-full"
                      style={{ width: `${metrics.market_demand_score || 0}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">Technical Level</span>
                    <span className="text-white font-bold">{metrics.technical_level_score?.toFixed(1) || 0}/100</span>
                  </div>
                  <div className="w-full bg-nvidia-lightGray rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${metrics.technical_level_score || 0}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-400">Partnership Potential</span>
                    <span className="text-white font-bold">{metrics.partnership_potential_score?.toFixed(1) || 0}/100</span>
                  </div>
                  <div className="w-full bg-nvidia-lightGray rounded-full h-2">
                    <div
                      className="bg-purple-500 h-2 rounded-full"
                      style={{ width: `${metrics.partnership_potential_score || 0}%` }}
                    />
                  </div>
                </div>

                <div className="pt-2 border-t border-nvidia-lightGray">
                  <div className="flex justify-between">
                    <span className="text-gray-400 font-semibold">Total Score</span>
                    <span className="text-nvidia-green font-bold text-xl">{metrics.total_score?.toFixed(1) || 0}/100</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommendation */}
      {analysis?.recommendation && (
        <div className="bg-nvidia-gray rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">AI Recommendation</h2>
          <p className="text-gray-300">{analysis.recommendation}</p>
        </div>
      )}

      {/* Metadata */}
      <div className="bg-nvidia-gray rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Additional Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex justify-between">
            <span className="text-gray-400">Added to Database</span>
            <span className="text-white">{format(new Date(startup.created_at), 'MMM dd, yyyy HH:mm')}</span>
          </div>
          {startup.updated_at && (
            <div className="flex justify-between">
              <span className="text-gray-400">Last Updated</span>
              <span className="text-white">{format(new Date(startup.updated_at), 'MMM dd, yyyy HH:mm')}</span>
            </div>
          )}
          {analysis?.analysis_date && (
            <div className="flex justify-between">
              <span className="text-gray-400">Analysis Date</span>
              <span className="text-white">{format(new Date(analysis.analysis_date), 'MMM dd, yyyy')}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default StartupDetail;
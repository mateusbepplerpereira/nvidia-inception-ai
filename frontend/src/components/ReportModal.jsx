import { useState, useRef, useEffect } from 'react';
import { reportService } from '../services/api';

const ReportModal = ({
  isOpen,
  onClose,
  availableMetrics,
  title = "Gerar Relatório de Startups"
}) => {
  const [reportFilters, setReportFilters] = useState({
    sectors: [],
    technologies: [],
    countries: [],
    maxStartups: 50,
    sortBy: 'score',
    sortOrder: 'desc',
    startDate: '',
    endDate: ''
  });
  const [generatingReport, setGeneratingReport] = useState(false);

  const sectorsSelectRef = useRef(null);
  const technologiesSelectRef = useRef(null);
  const countriesSelectRef = useRef(null);

  // Initialize select2 when modal opens
  useEffect(() => {
    if (isOpen && window.$) {
      // Use requestAnimationFrame to ensure DOM is ready
      const initializeSelect2 = () => {
        // Initialize sectors select2
        if (sectorsSelectRef.current && !window.$(sectorsSelectRef.current).hasClass('select2-hidden-accessible')) {
          window.$(sectorsSelectRef.current).select2({
            theme: 'classic',
            placeholder: 'Digite para buscar setores...',
            allowClear: true,
            width: '100%',
            dropdownAutoWidth: false,
            minimumInputLength: 0,
            closeOnSelect: false,
            dropdownParent: window.$(sectorsSelectRef.current).closest('.bg-nvidia-gray'),
            escapeMarkup: function(markup) { return markup; },
            containerCssClass: 'select2-container-custom',
            dropdownCssClass: 'select2-dropdown-custom'
          }).on('change', function() {
            const values = window.$(this).val() || [];
            setReportFilters(prev => ({ ...prev, sectors: values }));
          }).on('select2:open', function() {
            // Force search field to be visible and focused
            setTimeout(() => {
              const searchField = window.$(this).next('.select2-container').find('.select2-search__field');
              searchField.focus();
              searchField.attr('placeholder', 'Digite para buscar setores...');
            }, 10);
          }).on('select2:select select2:unselect', function() {
            // Força placeholder após seleção/deseleção
            setTimeout(() => {
              const searchField = window.$(this).next('.select2-container').find('.select2-search__field');
              searchField.attr('placeholder', 'Digite para buscar setores...');
            }, 50);
          });
        }

        // Initialize technologies select2
        if (technologiesSelectRef.current && !window.$(technologiesSelectRef.current).hasClass('select2-hidden-accessible')) {
          window.$(technologiesSelectRef.current).select2({
            theme: 'classic',
            placeholder: 'Digite para buscar tecnologias...',
            allowClear: true,
            width: '100%',
            dropdownAutoWidth: false,
            minimumInputLength: 0,
            closeOnSelect: false,
            dropdownParent: window.$(technologiesSelectRef.current).closest('.bg-nvidia-gray'),
            escapeMarkup: function(markup) { return markup; },
            containerCssClass: 'select2-container-custom',
            dropdownCssClass: 'select2-dropdown-custom'
          }).on('change', function() {
            const values = window.$(this).val() || [];
            setReportFilters(prev => ({ ...prev, technologies: values }));
          }).on('select2:open', function() {
            // Force search field to be visible and focused
            setTimeout(() => {
              const searchField = window.$(this).next('.select2-container').find('.select2-search__field');
              searchField.focus();
              searchField.attr('placeholder', 'Digite para buscar tecnologias...');
            }, 10);
          }).on('select2:select select2:unselect', function() {
            // Força placeholder após seleção/deseleção
            setTimeout(() => {
              const searchField = window.$(this).next('.select2-container').find('.select2-search__field');
              searchField.attr('placeholder', 'Digite para buscar tecnologias...');
            }, 50);
          });
        }

        // Initialize countries select2
        if (countriesSelectRef.current && !window.$(countriesSelectRef.current).hasClass('select2-hidden-accessible')) {
          window.$(countriesSelectRef.current).select2({
            theme: 'classic',
            placeholder: 'Digite para buscar países...',
            allowClear: true,
            width: '100%',
            dropdownAutoWidth: false,
            minimumInputLength: 0,
            closeOnSelect: false,
            dropdownParent: window.$(countriesSelectRef.current).closest('.bg-nvidia-gray'),
            escapeMarkup: function(markup) { return markup; },
            containerCssClass: 'select2-container-custom',
            dropdownCssClass: 'select2-dropdown-custom'
          }).on('change', function() {
            const values = window.$(this).val() || [];
            setReportFilters(prev => ({ ...prev, countries: values }));
          }).on('select2:open', function() {
            // Force search field to be visible and focused
            setTimeout(() => {
              const searchField = window.$(this).next('.select2-container').find('.select2-search__field');
              searchField.focus();
              searchField.attr('placeholder', 'Digite para buscar países...');
            }, 10);
          }).on('select2:select select2:unselect', function() {
            // Força placeholder após seleção/deseleção
            setTimeout(() => {
              const searchField = window.$(this).next('.select2-container').find('.select2-search__field');
              searchField.attr('placeholder', 'Digite para buscar países...');
            }, 50);
          });
        }
      };

      // Use multiple frames to ensure everything is rendered
      requestAnimationFrame(() => {
        requestAnimationFrame(initializeSelect2);
      });
    }

    // Cleanup select2 when modal closes
    if (!isOpen && window.$) {
      if (sectorsSelectRef.current && window.$(sectorsSelectRef.current).hasClass('select2-hidden-accessible')) {
        try {
          window.$(sectorsSelectRef.current).select2('destroy');
        } catch (e) {
          console.log('Error destroying sectors select2:', e);
        }
      }
      if (technologiesSelectRef.current && window.$(technologiesSelectRef.current).hasClass('select2-hidden-accessible')) {
        try {
          window.$(technologiesSelectRef.current).select2('destroy');
        } catch (e) {
          console.log('Error destroying technologies select2:', e);
        }
      }
      if (countriesSelectRef.current && window.$(countriesSelectRef.current).hasClass('select2-hidden-accessible')) {
        try {
          window.$(countriesSelectRef.current).select2('destroy');
        } catch (e) {
          console.log('Error destroying countries select2:', e);
        }
      }
    }
  }, [isOpen]);

  const generateReport = async () => {
    try {
      setGeneratingReport(true);

      const reportParams = {
        sectors: reportFilters.sectors.length > 0 ? reportFilters.sectors : [],
        technologies: reportFilters.technologies.length > 0 ? reportFilters.technologies : [],
        countries: reportFilters.countries.length > 0 ? reportFilters.countries : [],
        max_startups: reportFilters.maxStartups,
        sort_by: reportFilters.sortBy,
        sort_order: reportFilters.sortOrder,
        start_date: reportFilters.startDate || null,
        end_date: reportFilters.endDate || null
      };

      const blob = await reportService.generateReport(reportParams);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `relatorio_startups_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      onClose();
    } catch (error) {
      console.error('Erro ao gerar relatório:', error);
      alert('Erro ao gerar relatório. Tente novamente.');
    } finally {
      setGeneratingReport(false);
    }
  };

  // Função para verificar se há seleções
  const hasSelections = () => {
    return reportFilters.sectors.length > 0 ||
           reportFilters.technologies.length > 0 ||
           reportFilters.countries.length > 0;
  };

  // Adicionar estilos do scrollbar via useEffect
  useEffect(() => {
    if (isOpen) {
      const style = document.createElement('style');
      style.textContent = `
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #374151;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #76B900;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #5a8a00;
        }
        .select2-dropdown {
          background-color: #1f2937 !important;
          border: 1px solid #374151 !important;
        }
        .select2-dropdown .select2-results__option {
          color: white !important;
        }
        .select2-dropdown .select2-results__option--highlighted {
          background-color: #76B900 !important;
          color: black !important;
        }
        input[type="date"]::-webkit-calendar-picker-indicator {
          filter: invert(1);
          cursor: pointer;
        }
        input[type="number"]::-webkit-inner-spin-button,
        input[type="number"]::-webkit-outer-spin-button {
          opacity: 0.5;
        }
        /* Padronizar inputs e selects com select2 */
        input, select:not([multiple]) {
          background-color: rgb(45 45 45 / 1) !important;
          border: 1px solid #4A4A4A !important;
        }
        input:focus, select:not([multiple]):focus {
          border-color: #76B900 !important;
          box-shadow: 0 0 0 2px rgba(118, 185, 0, 0.2) !important;
        }
      `;
      document.head.appendChild(style);
      return () => {
        document.head.removeChild(style);
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" style={{marginTop: 0}}>
      <div className="bg-nvidia-gray rounded-lg p-6 w-full max-w-xl mx-4" style={{height: '90vh', display: 'flex', flexDirection: 'column'}}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">{title}</h2>
          <button
            onClick={onClose}
            className="text-white hover:text-nvidia-green transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
          <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Setores
              </label>
              <select
                ref={sectorsSelectRef}
                multiple
                className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green focus:border-transparent"
              >
                {availableMetrics?.sectors?.map(sector => (
                  <option key={sector} value={sector}>{sector}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Tecnologias
              </label>
              <select
                ref={technologiesSelectRef}
                multiple
                className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green focus:border-transparent"
              >
                {availableMetrics?.technologies?.map(tech => (
                  <option key={tech} value={tech}>{tech}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Países
              </label>
              <select
                ref={countriesSelectRef}
                multiple
                className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green focus:border-transparent"
              >
                {availableMetrics?.countries?.map(country => (
                  <option key={country} value={country}>{country}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Máximo de Startups
              </label>
              <input
                type="number"
                min="1"
                value={reportFilters.maxStartups}
                onChange={(e) => setReportFilters(prev => ({ ...prev, maxStartups: parseInt(e.target.value) || 50 }))}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green focus:border-transparent"
                placeholder="Ex: 50"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Ordenar por
              </label>
              <select
                value={reportFilters.sortBy}
                onChange={(e) => setReportFilters(prev => ({ ...prev, sortBy: e.target.value }))}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green focus:border-transparent"
              >
                <option value="score">Potencial Parceria</option>
                <option value="created_at">Data de Adição</option>
                <option value="name">Nome</option>
              </select>
            </div>

            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Ordem
              </label>
              <select
                value={reportFilters.sortOrder}
                onChange={(e) => setReportFilters(prev => ({ ...prev, sortOrder: e.target.value }))}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green focus:border-transparent"
              >
                <option value="desc">Decrescente</option>
                <option value="asc">Crescente</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Data de Início (opcional)
              </label>
              <input
                type="date"
                value={reportFilters.startDate}
                onChange={(e) => setReportFilters(prev => ({ ...prev, startDate: e.target.value }))}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Data de Fim (opcional)
              </label>
              <input
                type="date"
                value={reportFilters.endDate}
                onChange={(e) => setReportFilters(prev => ({ ...prev, endDate: e.target.value }))}
                className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-nvidia-green focus:border-transparent"
              />
            </div>
          </div>
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-6 pt-4 border-t border-gray-600 flex-shrink-0">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-300 hover:text-white transition-colors"
            disabled={generatingReport}
          >
            Cancelar
          </button>
          <button
            onClick={generateReport}
            disabled={generatingReport}
            className="px-6 py-2 bg-nvidia-green text-black font-medium rounded hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generatingReport ? 'Gerando...' : 'Gerar Relatório'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportModal;
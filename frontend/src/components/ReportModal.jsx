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
    maxStartups: 50
  });
  const [generatingReport, setGeneratingReport] = useState(false);

  const sectorsSelectRef = useRef(null);
  const technologiesSelectRef = useRef(null);

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
    }
  }, [isOpen]);

  const generateReport = async () => {
    try {
      setGeneratingReport(true);

      const reportParams = {
        sectors: reportFilters.sectors.length > 0 ? reportFilters.sectors : [],
        technologies: reportFilters.technologies.length > 0 ? reportFilters.technologies : [],
        max_startups: reportFilters.maxStartups
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" style={{marginTop: 0}}>
      <div className="bg-nvidia-gray rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
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

        <div className="space-y-6">
          <div>
            <label className="block text-white text-sm font-medium mb-2">
              Setores
            </label>
            <select
              ref={sectorsSelectRef}
              multiple
              className="w-full bg-gray-800 text-white border border-gray-600 rounded px-3 py-2"
            >
              {availableMetrics?.sectors?.map(sector => (
                <option key={sector} value={sector}>{sector}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-white text-sm font-medium mb-2">
              Tecnologias de IA
            </label>
            <select
              ref={technologiesSelectRef}
              multiple
              className="w-full bg-gray-800 text-white border border-gray-600 rounded px-3 py-2"
            >
              {availableMetrics?.technologies?.map(tech => (
                <option key={tech} value={tech}>{tech}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-white text-sm font-medium mb-2">
              Máximo de Startups
            </label>
            <select
              value={reportFilters.maxStartups}
              onChange={(e) => setReportFilters(prev => ({ ...prev, maxStartups: parseInt(e.target.value) }))}
              className="w-full bg-gray-800 text-white border border-gray-600 rounded px-3 py-2"
            >
              <option value={25}>25 startups</option>
              <option value={50}>50 startups</option>
              <option value={100}>100 startups</option>
              <option value={200}>200 startups</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-8">
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
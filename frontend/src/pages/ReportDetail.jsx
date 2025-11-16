import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Layout/Header';
import { getReportData, downloadReport } from '../utils/api';

function ReportDetail() {
  const { precheckId, fileType } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState(null);
  const [hasPdf, setHasPdf] = useState(false);
  const [reportStatus, setReportStatus] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await getReportData(precheckId, fileType);
        setReportData(data.report);
        setHasPdf(data.has_pdf);
        setReportStatus(data.status);
        setLoading(false);
      } catch (err) {
        console.error('Failed to load report:', err);
        setError('Failed to load report data');
        setLoading(false);
      }
    };

    fetchReport();
  }, [precheckId, fileType]);

  const formatFileType = (type) => {
    return type === 'site_plan' ? 'Site Plan' : 'Building Plan (PIM)';
  };

  const renderJsonSection = (title, data) => {
    if (!data) return null;

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">{title}</h2>
        <div className="space-y-4">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="border-b border-gray-200 pb-3 last:border-b-0">
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-colab-navy uppercase tracking-wide mb-1">
                  {key.replace(/_/g, ' ')}
                </span>
                <div className="text-gray-700">
                  {typeof value === 'object' && value !== null ? (
                    <div className="bg-gray-50 rounded p-3 mt-1">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(value, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <span className="text-base">{String(value)}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <div className="max-w-6xl mx-auto mt-20 p-4">
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-colab-blue mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading report...</h2>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <div className="max-w-6xl mx-auto mt-20 p-4">
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-2">Error</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={() => navigate(`/precheck/${precheckId}/results`)}
              className="btn-primary"
            >
              Back to Results
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />

      <div className="max-w-6xl mx-auto mt-8 p-4">
        {/* Header Section */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <button
              onClick={() => navigate(`/precheck/${precheckId}/results`)}
              className="text-colab-blue hover:text-colab-navy mb-2 flex items-center"
            >
              <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Results
            </button>
            <h1 className="text-3xl font-bold text-gray-900">
              {formatFileType(fileType)} - Compliance Report
            </h1>
          </div>
          {hasPdf && (
            <button
              onClick={() => downloadReport(precheckId, fileType)}
              className="btn-primary flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Download PDF Report</span>
            </button>
          )}
        </div>

        {/* Status Warning */}
        {reportStatus === 'review' && !reportData?.compliance && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  <strong>Note:</strong> Compliance check has not been completed yet. Only extracted components and enrichment data are available. The full compliance report will be generated after the compliance check completes.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Report Sections */}
        {reportData?.compliance && renderJsonSection('Compliance Check Results', reportData.compliance)}
        {reportData?.enriched && renderJsonSection('Enriched Analysis', reportData.enriched)}
        {reportData?.components && renderJsonSection('Extracted Components', reportData.components)}

        {/* No Data Message */}
        {!reportData?.compliance && !reportData?.enriched && !reportData?.components && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <p className="text-gray-600">No report data available</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ReportDetail;

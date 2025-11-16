import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Layout/Header';
import { getPreCheckStatus, getPreCheckData, downloadReport } from '../utils/api';

function Results() {
  const { precheckId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [precheck, setPrecheck] = useState(null);
  const [error, setError] = useState(null);
  const [processingStep, setProcessingStep] = useState('Initializing...');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let interval;

    const pollStatus = async () => {
      try {
        const statusData = await getPreCheckStatus(precheckId);

        // Update progress information
        if (statusData.processing_step) {
          setProcessingStep(statusData.processing_step);
        }
        if (statusData.progress !== undefined) {
          setProgress(statusData.progress);
        }

        if (statusData.status === 'completed') {
          // Get full precheck data
          const data = await getPreCheckData(precheckId);
          setPrecheck(data.precheck);
          setLoading(false);
          if (interval) clearInterval(interval);
        } else if (statusData.status === 'processing') {
          // Keep polling
          setLoading(true);
        } else {
          setError('Processing failed');
          setLoading(false);
          if (interval) clearInterval(interval);
        }
      } catch (err) {
        console.error('Failed to get status:', err);
        setError('Failed to load results');
        setLoading(false);
        if (interval) clearInterval(interval);
      }
    };

    // Initial poll
    pollStatus();

    // Poll every 3 seconds
    interval = setInterval(pollStatus, 3000);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [precheckId]);

  const getComplianceIcon = (status) => {
    if (status === 'completed') {
      return '✓';
    } else if (status === 'review' || status === 'REVIEW') {
      return '⚠️';
    } else if (status === 'failed') {
      return '✗';
    }
    return '?';
  };

  const getComplianceColor = (status) => {
    if (status === 'completed') return 'text-green-600';
    if (status === 'review' || status === 'REVIEW') return 'text-yellow-600';
    if (status === 'failed') return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <div className="max-w-4xl mx-auto mt-20 p-4">
          <div className="bg-white rounded-lg shadow-md p-12">
            <div className="text-center mb-8">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-colab-blue mx-auto mb-4"></div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Processing your documents...</h2>
              <p className="text-gray-600 mb-6">This may take 1-2 minutes. Please wait.</p>
            </div>

            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium text-colab-navy">{processingStep}</span>
                <span className="text-sm font-medium text-colab-navy">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-colab-blue h-3 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>

            {/* Processing Steps */}
            <div className="mt-8 space-y-3 text-sm">
              <div className={`flex items-center ${progress >= 10 ? 'text-green-600' : 'text-gray-400'}`}>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {progress >= 10 ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  )}
                </svg>
                <span>Preparing documents for analysis</span>
              </div>
              <div className={`flex items-center ${progress >= 25 ? 'text-green-600' : 'text-gray-400'}`}>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {progress >= 25 ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  )}
                </svg>
                <span>Extracting components from site plan</span>
              </div>
              <div className={`flex items-center ${progress >= 50 ? 'text-green-600' : 'text-gray-400'}`}>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {progress >= 50 ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  )}
                </svg>
                <span>Analyzing site plan compliance</span>
              </div>
              <div className={`flex items-center ${progress >= 100 ? 'text-green-600' : 'text-gray-400'}`}>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {progress >= 100 ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  )}
                </svg>
                <span>Generating compliance report</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <div className="max-w-4xl mx-auto mt-20 p-4">
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-2">Error</h2>
            <p className="text-gray-600">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const basicInfo = precheck?.basic_info || {};
  const results = precheck?.results || {};

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />

      <div className="max-w-6xl mx-auto mt-8 p-4">
        {/* Title */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {basicInfo.project_description || 'Pre-Check Results'}
          </h1>
          <p className="text-gray-600">{basicInfo.address}</p>
        </div>

        {/* Results Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Completeness Column */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Completeness</h2>

            <div className="space-y-4">
              {/* Form 2 */}
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-bold">
                  ✓
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Form 2</p>
                  <div className="mt-1 text-sm text-gray-500 space-y-1">
                    <div className="h-2 bg-gray-200 rounded"></div>
                    <div className="h-2 bg-gray-200 rounded"></div>
                    <div className="h-2 bg-gray-200 rounded w-3/4"></div>
                  </div>
                </div>
              </div>

              {/* Site plan */}
              <div className="flex items-start space-x-3">
                <div className={`flex-shrink-0 w-8 h-8 rounded-full ${results.site_plan ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'} flex items-center justify-center font-bold`}>
                  {results.site_plan ? '✓' : '✗'}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-gray-900">Site plan</p>
                    {results.site_plan && (
                      <button
                        onClick={() => downloadReport(precheckId, 'site_plan')}
                        className="text-colab-teal hover:text-colab-blue text-sm font-medium"
                      >
                        Remove/Upload
                      </button>
                    )}
                  </div>
                  {results.site_plan ? (
                    <div className="mt-1 text-sm text-gray-500 space-y-1">
                      <div className="h-2 bg-gray-200 rounded"></div>
                      <div className="h-2 bg-gray-200 rounded"></div>
                      <div className="h-2 bg-gray-200 rounded w-2/3"></div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 mt-1">Was not uploaded</p>
                  )}
                </div>
              </div>

              {/* PIM (Building Plan) */}
              <div className="flex items-start space-x-3">
                <div className={`flex-shrink-0 w-8 h-8 rounded-full ${results.building_plan ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'} flex items-center justify-center font-bold`}>
                  {results.building_plan ? '✓' : '✗'}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">PIM</p>
                  {results.building_plan ? (
                    <div className="mt-1 text-sm text-gray-500 space-y-1">
                      <div className="h-2 bg-gray-200 rounded"></div>
                      <div className="h-2 bg-gray-200 rounded"></div>
                      <div className="h-2 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 mt-1">Was not uploaded</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Compliance Column */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Compliance</h2>

            <div className="space-y-4">
              {/* Form 2 */}
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-bold">
                  ✓
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Form 2</p>
                  <div className="mt-1 text-sm text-gray-500 space-y-1">
                    <div className="h-2 bg-gray-200 rounded"></div>
                    <div className="h-2 bg-gray-200 rounded"></div>
                    <div className="h-2 bg-gray-200 rounded w-3/4"></div>
                  </div>
                </div>
              </div>

              {/* Site plan compliance */}
              {results.site_plan && (
                <div className="flex items-start space-x-3">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full ${results.site_plan.status === 'completed' ? 'bg-green-100' : 'bg-yellow-100'} flex items-center justify-center ${getComplianceColor(results.site_plan.status)} font-bold`}>
                    {getComplianceIcon(results.site_plan.status)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900">Site plan</p>
                      <button
                        onClick={() => navigate(`/precheck/${precheckId}/report/site_plan`)}
                        className="text-colab-blue hover:underline text-sm font-medium"
                      >
                        View Report
                      </button>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {results.site_plan.quality_score && `Quality: ${(results.site_plan.quality_score * 100).toFixed(0)}%`}
                    </p>
                    <div className="mt-1 text-sm text-gray-500 space-y-1">
                      <div className="h-2 bg-gray-200 rounded"></div>
                      <div className="h-2 bg-gray-200 rounded"></div>
                      <div className="h-2 bg-gray-200 rounded w-2/3"></div>
                    </div>
                  </div>
                </div>
              )}

              {/* PIM compliance */}
              {results.building_plan && (
                <div className="flex items-start space-x-3">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full ${results.building_plan.status === 'completed' ? 'bg-green-100' : 'bg-yellow-100'} flex items-center justify-center ${getComplianceColor(results.building_plan.status)} font-bold`}>
                    {getComplianceIcon(results.building_plan.status)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900">PIM</p>
                      <button
                        onClick={() => navigate(`/precheck/${precheckId}/report/building_plan`)}
                        className="text-colab-blue hover:underline text-sm font-medium"
                      >
                        View Report
                      </button>
                    </div>
                    <div className="mt-1 text-sm text-gray-500 space-y-1">
                      <div className="h-2 bg-gray-200 rounded"></div>
                      <div className="h-2 bg-gray-200 rounded"></div>
                      <div className="h-2 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Results;

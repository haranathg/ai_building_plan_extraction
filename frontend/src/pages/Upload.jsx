import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ProgressStepper from '../components/Stepper/ProgressStepper';
import { uploadFiles, processPreCheck } from '../utils/api';

function Upload() {
  const navigate = useNavigate();
  const { precheckId } = useParams();
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState({
    drainage_plan: null,
    site_plan: null,
    record_of_title: null,
    agent_consent: null,
    building_plan: null
  });

  const handleFileChange = (fileType, event) => {
    const file = event.target.files[0];
    if (file) {
      // Check if it's a PDF
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please upload only PDF files');
        return;
      }
      setFiles({
        ...files,
        [fileType]: file
      });
    }
  };

  const handleNext = async () => {
    // Check if at least site_plan is uploaded
    if (!files.site_plan) {
      alert('Site plan is required');
      return;
    }

    setLoading(true);
    try {
      // Upload files
      await uploadFiles(precheckId, files);

      // Start processing
      await processPreCheck(precheckId);

      // Navigate to results page
      navigate(`/precheck/${precheckId}/results`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload files. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDraft = () => {
    alert('Draft saved successfully!');
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-2xl mx-auto p-4">
        {/* Card */}
        <div className="bg-white rounded-lg shadow-md p-8">
          {/* Title */}
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            New Pre-Check
          </h2>

          {/* Progress Stepper */}
          <ProgressStepper currentStep={2} />

          {/* Instructions */}
          <p className="text-gray-700 mb-6 mt-8">
            You will need the following documents. Please upload and I will do a quick check
          </p>

          {/* File Upload List */}
          <div className="space-y-4">
            {/* Drainage/plumbing plan */}
            <div className="flex items-center justify-between">
              <span className="text-gray-700">• Drainage /plumbing plan</span>
              <label className="btn-secondary cursor-pointer flex items-center space-x-2 px-4 py-2 text-sm">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span>{files.drainage_plan ? files.drainage_plan.name : 'Choose file'}</span>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFileChange('drainage_plan', e)}
                  className="hidden"
                />
              </label>
            </div>

            {/* Site plan */}
            <div className="flex items-center justify-between">
              <span className="text-gray-700">
                • Site plan <span className="text-red-500">*</span>
              </span>
              <label className="btn-secondary cursor-pointer flex items-center space-x-2 px-4 py-2 text-sm">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span>{files.site_plan ? files.site_plan.name : 'Choose file'}</span>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFileChange('site_plan', e)}
                  className="hidden"
                />
              </label>
            </div>

            {/* Building plan (optional) */}
            <div className="flex items-center justify-between">
              <span className="text-gray-700">• Building plan (optional)</span>
              <label className="btn-secondary cursor-pointer flex items-center space-x-2 px-4 py-2 text-sm">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span>{files.building_plan ? files.building_plan.name : 'Choose file'}</span>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFileChange('building_plan', e)}
                  className="hidden"
                />
              </label>
            </div>

            {/* Record of title */}
            <div className="flex items-center justify-between">
              <span className="text-gray-700">• Record of title</span>
              <label className="btn-secondary cursor-pointer flex items-center space-x-2 px-4 py-2 text-sm">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span>{files.record_of_title ? files.record_of_title.name : 'Choose file'}</span>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFileChange('record_of_title', e)}
                  className="hidden"
                />
              </label>
            </div>

            {/* Agent consent */}
            <div className="flex items-center justify-between">
              <span className="text-gray-700">• Agent consent</span>
              <label className="btn-secondary cursor-pointer flex items-center space-x-2 px-4 py-2 text-sm">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span>{files.agent_consent ? files.agent_consent.name : 'Choose file'}</span>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFileChange('agent_consent', e)}
                  className="hidden"
                />
              </label>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex justify-between mt-8">
            <button
              onClick={handleSaveDraft}
              className="bg-gray-400 text-white px-8 py-3 rounded-lg font-semibold hover:bg-gray-500 transition"
            >
              Save Draft
            </button>
            <button
              onClick={handleNext}
              disabled={loading || !files.site_plan}
              className={loading || !files.site_plan ? 'btn-disabled px-8' : 'btn-primary px-8'}
            >
              {loading ? 'Processing...' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Upload;

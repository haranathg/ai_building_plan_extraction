import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ProgressStepper from '../components/Stepper/ProgressStepper';
import { createPreCheck, saveBasicInfo } from '../utils/api';

function BasicInfo() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [precheckId, setPrecheckId] = useState(null);
  const [formData, setFormData] = useState({
    project_description: '',
    address: '',
    consent_type: 'building_consent_only',
    use_bedrock_kb: false
  });

  useEffect(() => {
    // Create precheck on mount
    const initPrecheck = async () => {
      try {
        const data = await createPreCheck();
        setPrecheckId(data.precheck_id);
        // Store in session
        sessionStorage.setItem('precheckId', data.precheck_id);
      } catch (error) {
        console.error('Failed to create precheck:', error);
      }
    };
    initPrecheck();
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleNext = async () => {
    if (!formData.project_description || !formData.address) {
      alert('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      await saveBasicInfo(precheckId, formData);
      // Store form data in session
      sessionStorage.setItem('basicInfo', JSON.stringify(formData));
      // Navigate to upload page
      navigate(`/precheck/${precheckId}/upload`);
    } catch (error) {
      console.error('Failed to save basic info:', error);
      alert('Failed to save. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!precheckId) return;

    try {
      await saveBasicInfo(precheckId, formData);
      alert('Draft saved successfully!');
    } catch (error) {
      console.error('Failed to save draft:', error);
    }
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
          <ProgressStepper currentStep={1} />

          {/* Form */}
          <div className="space-y-6 mt-8">
            {/* Project Description */}
            <div>
              <label className="block text-gray-700 font-medium mb-2">
                What are you planning to do?
              </label>
              <input
                type="text"
                name="project_description"
                value={formData.project_description}
                onChange={handleChange}
                placeholder="Tell us about your project"
                className="input-field"
                required
              />
            </div>

            {/* Address */}
            <div>
              <label className="block text-gray-700 font-medium mb-2">
                What is the address?
              </label>
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="Type your address..."
                className="input-field"
                required
              />
            </div>

            {/* Consent Type */}
            <div>
              <label className="block text-gray-700 font-medium mb-2">
                Do you need a PIM or BC only?
              </label>
              <select
                name="consent_type"
                value={formData.consent_type}
                onChange={handleChange}
                className="input-field"
              >
                <option value="building_consent_only">Building consent only</option>
                <option value="pim_only">PIM only</option>
                <option value="both">Both PIM and BC</option>
              </select>
            </div>

            {/* Bedrock KB Toggle */}
            <div className="mb-6">
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex-1">
                  <label className="block text-gray-700 font-medium mb-1">
                    Use AWS Bedrock Knowledge Base
                  </label>
                  <p className="text-sm text-gray-600">
                    Enable to use AWS Bedrock Knowledge Base for compliance checking instead of Neo4j + Pinecone
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={formData.use_bedrock_kb}
                    onChange={(e) => setFormData({...formData, use_bedrock_kb: e.target.checked})}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
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
              disabled={loading}
              className={loading ? 'btn-disabled px-8' : 'btn-primary px-8'}
            >
              {loading ? 'Saving...' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BasicInfo;

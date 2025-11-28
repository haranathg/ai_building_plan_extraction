import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validateAccessKey } from '../utils/api';
import urbanCompassLogo from '../assets/urbancompass.jpg';

function Login() {
  const navigate = useNavigate();
  const [accessKey, setAccessKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await validateAccessKey(accessKey);
      // Store auth info
      localStorage.setItem('authenticated', 'true');
      localStorage.setItem('accessLevel', data.access_level || 'beta');
      localStorage.setItem('authExpiry', data.expiry || '');
      // Navigate to dashboard
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid access key. Please check your key and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-colab-navy to-blue-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
        {/* Urban Compass Logo */}
        <div className="flex justify-center mb-6">
          <a
            href="https://urbancompass.com"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:opacity-80 transition-opacity"
          >
            <img
              src={urbanCompassLogo}
              alt="Urban Compass"
              className="h-16 w-auto"
            />
          </a>
        </div>

        {/* CoLabs Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold">
            <span className="text-colab-navy">CO</span>
            <span className="text-colab-orange">LAB</span>
          </h1>
          <p className="text-gray-500 text-sm mt-1">BETTER TOGETHER</p>
        </div>

        {/* App Title */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-colab-navy">
            CompliCheck AI
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Building Consent Pre-Check System
          </p>
        </div>

        {/* Beta Badge */}
        <div className="flex justify-center mb-6">
          <span className="px-4 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-semibold border border-yellow-300">
            BETA ACCESS
          </span>
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 text-center">
          Enter Access Key
        </h3>
        <p className="text-gray-600 mb-6 text-center text-sm">
          This is a private beta. Enter your access key to continue.
        </p>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-gray-700 font-medium mb-2">
              Access Key
            </label>
            <input
              type="password"
              value={accessKey}
              onChange={(e) => setAccessKey(e.target.value)}
              placeholder="Enter your access key"
              className="input-field font-mono text-center tracking-wider"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={loading ? 'btn-disabled w-full' : 'btn-primary w-full'}
          >
            {loading ? 'Validating...' : 'Access CompliCheck'}
          </button>
        </form>

        {/* Info */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Don't have an access key?</p>
          <p className="mt-1">
            Contact{' '}
            <a href="mailto:support@colabs.co.nz" className="text-colab-blue hover:underline">
              support@colabs.co.nz
            </a>
          </p>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-gray-200 text-center text-xs text-gray-400">
          <p>&copy; 2024 CoLabs. All rights reserved.</p>
          <p className="mt-1">Powered by AI for smarter building compliance.</p>
        </div>
      </div>
    </div>
  );
}

export default Login;

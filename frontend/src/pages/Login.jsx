import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../utils/api';

function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await login(username, password);
      // Store user info
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('token', data.token);
      // Navigate to dashboard
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-md p-8 w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold">
            <span className="text-colab-navy">CO</span>
            <span className="text-colab-orange">LAB</span>
          </h1>
          <p className="text-gray-500 text-sm mt-1">BETTER TOGETHER</p>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Login to your account
        </h2>
        <p className="text-gray-600 mb-6">
          Use your username and password to login
        </p>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 font-medium mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 font-medium mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={loading ? 'btn-disabled w-full' : 'btn-primary w-full'}
          >
            {loading ? 'Logging in...' : 'Log in'}
          </button>
        </form>

        {/* Links */}
        <div className="mt-4 text-center">
          <a href="#" className="text-colab-blue hover:underline text-sm">
            Forgot password?
          </a>
        </div>

        <div className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <a href="#" className="text-colab-blue hover:underline font-medium">
            Create account
          </a>
        </div>
      </div>
    </div>
  );
}

export default Login;

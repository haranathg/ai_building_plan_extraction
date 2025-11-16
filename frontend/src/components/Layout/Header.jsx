import { useNavigate } from 'react-router-dom';

function Header() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <header className="bg-colab-navy text-white py-4 px-6">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        {/* Logo */}
        <div className="flex items-center space-x-2">
          <h1 className="text-2xl font-bold">
            <span className="text-white">CO</span>
            <span className="text-colab-orange">LAB</span>
          </h1>
          <span className="text-xs text-gray-300">BETTER TOGETHER</span>
        </div>

        {/* User Menu */}
        <div className="flex items-center space-x-4">
          <span className="text-sm">{user.username || 'User'}</span>
          <button
            onClick={handleLogout}
            className="bg-white bg-opacity-10 hover:bg-opacity-20 rounded-full p-2 transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;

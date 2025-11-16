import { useNavigate } from 'react-router-dom';
import Header from '../components/Layout/Header';

function Dashboard() {
  const navigate = useNavigate();

  const handleNewPreCheck = () => {
    navigate('/precheck/new');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />

      <div className="max-w-2xl mx-auto mt-20 p-4">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Select an option
          </h2>

          <div className="space-y-4">
            {/* New pre-check button */}
            <button
              onClick={handleNewPreCheck}
              className="btn-primary w-full text-lg py-4"
            >
              New pre-check
            </button>

            {/* Continue save/Draft pre-check button */}
            <button
              disabled
              className="btn-secondary w-full text-lg py-4"
            >
              Continue save/Draft pre-check
            </button>

            {/* Template pre-check application button */}
            <button
              disabled
              className="btn-primary w-full text-lg py-4"
            >
              Template pre-check application
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import BasicInfo from './pages/BasicInfo';
import Upload from './pages/Upload';
import Results from './pages/Results';
import ReportDetail from './pages/ReportDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/precheck/new" element={<BasicInfo />} />
        <Route path="/precheck/:precheckId/upload" element={<Upload />} />
        <Route path="/precheck/:precheckId/results" element={<Results />} />
        <Route path="/precheck/:precheckId/report/:fileType" element={<ReportDetail />} />
      </Routes>
    </Router>
  );
}

export default App;

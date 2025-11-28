import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import BasicInfo from './pages/BasicInfo';
import Upload from './pages/Upload';
import Results from './pages/Results';
import ReportDetail from './pages/ReportDetail';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/precheck/new" element={
          <ProtectedRoute>
            <BasicInfo />
          </ProtectedRoute>
        } />
        <Route path="/precheck/:precheckId/upload" element={
          <ProtectedRoute>
            <Upload />
          </ProtectedRoute>
        } />
        <Route path="/precheck/:precheckId/results" element={
          <ProtectedRoute>
            <Results />
          </ProtectedRoute>
        } />
        <Route path="/precheck/:precheckId/report/:fileType" element={
          <ProtectedRoute>
            <ReportDetail />
          </ProtectedRoute>
        } />
      </Routes>
    </Router>
  );
}

export default App;

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Startups from './pages/Startups';
import StartupDetail from './pages/StartupDetail';
import Settings from './pages/Settings';
import Logs from './pages/Logs';
import { NotificationProvider } from './contexts/NotificationContext';

function App() {
  return (
    <NotificationProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="startups" element={<Startups />} />
            <Route path="startups/:id" element={<StartupDetail />} />
            <Route path="settings" element={<Settings />} />
            <Route path="logs" element={<Logs />} />
          </Route>
        </Routes>
      </Router>
    </NotificationProvider>
  );
}

export default App

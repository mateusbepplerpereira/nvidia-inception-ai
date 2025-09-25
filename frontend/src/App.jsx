import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Startups from './pages/Startups';
import StartupDetail from './pages/StartupDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="startups" element={<Startups />} />
          <Route path="startups/:id" element={<StartupDetail />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App

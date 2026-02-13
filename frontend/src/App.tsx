import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from './components/ui';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import CVEditor from './pages/CVEditor';
import Sources from './pages/Sources';
import Jobs from './pages/Jobs';
import SettingsPage from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cv" element={<CVEditor />} />
          <Route path="/sources" element={<Sources />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 5000,
          style: {
            fontFamily: "'Inter', sans-serif",
            fontSize: '14px',
          },
        }}
      />
    </BrowserRouter>
  );
}

import { Routes, Route } from 'react-router-dom';
import { AppProvider } from '@/contexts/AppContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ToastProvider } from '@/contexts/ToastContext';
import Layout from '@/components/Layout';
import ToastContainer from '@/components/ToastContainer';
import DownloadPage from '@/pages/DownloadPage';
import VideoListPage from '@/pages/VideoListPage';
import PlayerPage from '@/pages/PlayerPage';
import NotFoundPage from '@/pages/NotFoundPage';
import { ComponentDemoPage } from '@/pages/ComponentDemoPage';

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AppProvider>
          <Layout>
            <Routes>
              <Route path="/" element={<VideoListPage />} />
              <Route path="/downloads" element={<DownloadPage />} />
              <Route path="/player/:videoId" element={<PlayerPage />} />
              <Route path="/demo" element={<ComponentDemoPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Layout>
          <ToastContainer />
        </AppProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
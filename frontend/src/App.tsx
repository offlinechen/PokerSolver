import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import HandEditorPage from './pages/HandEditorPage';
import AnalysisResultPage from './pages/AnalysisResultPage';
import HistoryPage from './pages/HistoryPage';
import ReplayPage from './pages/ReplayPage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/hand/new" element={<HandEditorPage />} />
        <Route path="/hand/:id" element={<AnalysisResultPage />} />
        <Route path="/hand/:id/replay" element={<ReplayPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Route>
    </Routes>
  );
}

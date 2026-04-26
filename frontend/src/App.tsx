import { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Activity } from 'lucide-react';
import { apiService } from './services/api';
import Navbar from './components/Layout/Navbar';
import HeroView from './components/Views/HeroView';
import AnalysisView from './components/Views/AnalysisView';

export interface AnalysisData {
  query: string;
  response: string;
  risk_profile?: Record<string, any>;
  timestamp: string;
  isError?: boolean;
}

export default function App() {
  const [query, setQuery] = useState('');
  const [view, setView] = useState<'hero' | 'analysis'>('hero');
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisData | null>(null);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const savedHistory = sessionStorage.getItem('cryptodd_history');
    if (savedHistory) {
      setSearchHistory(JSON.parse(savedHistory));
    }
    const savedAnalysis = sessionStorage.getItem('cryptodd_current');
    if (savedAnalysis) {
      setCurrentAnalysis(JSON.parse(savedAnalysis));
      setView('analysis');
    }
  }, []);

  const saveState = (history: string[], analysis: AnalysisData | null) => {
    sessionStorage.setItem('cryptodd_history', JSON.stringify(history));
    if (analysis) {
      sessionStorage.setItem('cryptodd_current', JSON.stringify(analysis));
    } else {
      sessionStorage.removeItem('cryptodd_current');
    }
  };

  const handleVerify = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setView('analysis');
    setQuery(''); // Clear the input field immediately
    
    // Set a temporary loading state for the current analysis
    setCurrentAnalysis({
      query: searchQuery,
      response: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });

    try {
      // Notice we are no longer sending threadId as this is a stateless, single-shot dashboard
      const data = await apiService.chat(searchQuery);
      
      const newAnalysis: AnalysisData = {
        query: searchQuery,
        response: data.response,
        risk_profile: data.risk_profile,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setCurrentAnalysis(newAnalysis);

      // Update history: Add to front, remove duplicates, keep only last 5
      const updatedHistory = [searchQuery, ...searchHistory.filter(q => q.toLowerCase() !== searchQuery.toLowerCase())].slice(0, 5);
      setSearchHistory(updatedHistory);
      
      saveState(updatedHistory, newAnalysis);
    } catch {
      const errorAnalysis: AnalysisData = {
        query: searchQuery,
        response: '🚨 Connection failed. Check that the backend is running.',
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setCurrentAnalysis(errorAnalysis);
      saveState(searchHistory, errorAnalysis);
    } finally {
      setIsLoading(false);
    }
  };

  const resetPlatform = () => {
    sessionStorage.removeItem('cryptodd_current');
    sessionStorage.removeItem('cryptodd_history');
    setCurrentAnalysis(null);
    setSearchHistory([]);
    setView('hero');
    setQuery('');
  };

  return (
    <div 
      className="min-h-screen flex flex-col relative" 
      data-theme={theme}
      style={{ background: 'var(--bg)', color: 'var(--text)', transition: 'background 0.3s, color 0.3s' }}
    >
      <Navbar
        theme={theme}
        setTheme={setTheme}
        onReset={resetPlatform}
        onSearch={handleVerify}
        isLoading={isLoading}
        showSearch={view === 'analysis'}
      />

      <main className="flex-1 flex overflow-hidden pt-16">
        <div className="flex-1 flex flex-col relative overflow-hidden">
          <AnimatePresence mode="wait">
            {view === 'hero' ? (
              <HeroView
                key="hero"
                query={query}
                setQuery={setQuery}
                onVerify={() => handleVerify(query)}
              />
            ) : (
              <AnalysisView
                key="analysis"
                analysis={currentAnalysis}
                isLoading={isLoading}
              />
            )}
          </AnimatePresence>
        </div>

        {/* ── Right Sidebar: Recent Searches (Analysis View Only, 2+ searches) ── */}
        {view === 'analysis' && searchHistory.length >= 2 && (
          <aside 
            className="recent-searches-sidebar"
          >
            <div className="sidebar-header">
              <Activity size={14} style={{ color: 'var(--accent)' }} />
              Recent Activity
            </div>

            <div className="sidebar-content">
              {searchHistory.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleVerify(q)}
                  className="history-item"
                >
                  <div className="history-icon-bg">
                    <Activity size={14} />
                  </div>
                  <div className="history-text">
                    <span className="history-query">{q}</span>
                    <span className="history-hint">Click to re-analyze</span>
                  </div>
                </button>
              ))}
            </div>
          </aside>
        )}
      </main>
    </div>
  );
}

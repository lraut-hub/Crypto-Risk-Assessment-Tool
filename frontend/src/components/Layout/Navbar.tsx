import React, { useState, useEffect } from 'react';
import { Sun, Moon, Shield, RotateCcw, Activity } from 'lucide-react';

interface NavbarProps {
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  onReset: () => void;
  onSearch: (query: string) => void;
  isLoading: boolean;
  showSearch: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ theme, setTheme, onReset, onSearch, isLoading, showSearch }) => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
        const response = await fetch(`${API_BASE}/health`);
        setIsHealthy(response.ok);
      } catch {
        setIsHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onSearch(searchQuery);
      setSearchQuery('');
    }
  };
  return (
    <header
      className="fixed top-0 left-0 right-0 z-50"
      style={{ background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}
    >
      <div
        className="flex items-center relative"
        style={{ 
          width: '100%',
          padding: '0 var(--space-5)', // Increased side padding for a premium look
          height: 64,
          position: 'relative',
          zIndex: 10
        }}
      >
        {/* Left: Logo (Anchored to Far Left) */}
        <div className="flex-1 flex justify-start">
          <button
            onClick={onReset}
            className="flex items-center cursor-pointer bg-transparent border-none"
            style={{ 
              color: 'var(--text)', 
              gap: 12,
              padding: '4px 10px',
              borderRadius: 'var(--radius)',
              marginLeft: '-10px' // Slightly closer to edge for extreme-left look
            }}
          >
            <div
              className="flex items-center justify-center"
              style={{
                width: 36,
                height: 36,
                borderRadius: 'var(--radius)',
                background: 'var(--accent)',
                boxShadow: '0 4px 12px rgba(var(--accent-rgb), 0.2)'
              }}
            >
              <Shield size={18} color="white" />
            </div>
            <div className="flex flex-col items-start text-left">
              <span style={{ fontSize: 17, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.1 }}>
                Crypto<span style={{ color: 'var(--accent)' }}>DD</span>
              </span>
              <span style={{ fontSize: 10, opacity: 0.6, fontWeight: 600, letterSpacing: '0.05em', marginTop: 2 }}>
                DUE DILIGENCE
              </span>
            </div>
          </button>
        </div>

        {/* Middle: Absolute Search Bar (Placeholder for flex spacing) */}
        <div className="flex-none" style={{ width: 480 }}></div>

        {/* Right: Action Cluster (Anchored to Far Right) */}
        <div className="flex-1 flex justify-end items-center" style={{ gap: 'var(--space-2)', zIndex: 60 }}>
          {/* Live Status */}
          {isHealthy !== null && (
            <div 
              title={isHealthy ? "Backend Connected" : "Backend Disconnected"}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 14px',
                borderRadius: '10px',
                background: isHealthy ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                border: `1px solid ${isHealthy ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                color: isHealthy ? '#22c55e' : '#ef4444',
                fontSize: 11,
                fontWeight: 800,
                letterSpacing: '0.05em',
                marginRight: 8
              }}
            >
              <div 
                style={{ 
                  width: 6, 
                  height: 6, 
                  borderRadius: '50%', 
                  background: 'currentColor',
                  boxShadow: isHealthy ? '0 0 10px #22c55e' : 'none'
                }} 
                className={isHealthy ? "pulse-dot" : ""}
              />
              {isHealthy ? "LIVE" : "OFFLINE"}
            </div>
          )}

          {/* New Session */}
          <button
            onClick={onReset}
            title="New session"
            className="flex items-center justify-center cursor-pointer"
            style={{
              width: 38,
              height: 38,
              borderRadius: '12px',
              background: 'var(--bg-raised)',
              border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--accent)';
              e.currentTarget.style.borderColor = 'var(--accent)';
              e.currentTarget.style.background = 'var(--accent-muted)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--text-secondary)';
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.background = 'var(--bg-raised)';
            }}
          >
            <RotateCcw size={16} />
          </button>

          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="flex items-center justify-center cursor-pointer"
            style={{
              width: 38,
              height: 38,
              borderRadius: '12px',
              background: 'var(--bg-raised)',
              border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--accent)';
              e.currentTarget.style.borderColor = 'var(--accent)';
              e.currentTarget.style.background = 'var(--accent-muted)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--text-secondary)';
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.background = 'var(--bg-raised)';
            }}
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>

      {/* SEARCH BAR: Placed at the root of the header for true viewport centering */}
      <div 
        style={{ 
          position: 'absolute',
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)',
          width: '100%', 
          maxWidth: 480, 
          opacity: showSearch ? 1 : 0, 
          pointerEvents: showSearch ? 'auto' : 'none',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          zIndex: 50
        }}
      >
        <form 
          onSubmit={handleSearchSubmit}
          style={{
            width: '100%',
            position: 'relative',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <div style={{ position: 'absolute', left: 16, color: 'var(--text-secondary)', display: 'flex' }}>
            <Activity size={15} className={isLoading ? "spin" : ""} />
          </div>
          <input
            type="text"
            placeholder="Search token or address..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '13px 18px 13px 48px',
              background: 'var(--bg-raised)',
              border: '1px solid var(--border)',
              borderRadius: '14px',
              color: 'var(--text)',
              fontSize: 14,
              fontWeight: 500,
              outline: 'none',
              transition: 'all 0.2s',
              boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent)';
              e.currentTarget.style.boxShadow = '0 0 0 4px var(--accent-muted), 0 8px 30px rgba(0,0,0,0.2)';
              e.currentTarget.style.background = 'var(--bg)';
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';
              e.currentTarget.style.background = 'var(--bg-raised)';
            }}
          />
        </form>
      </div>
    </header>
  );
};

export default Navbar;

import React, { useState } from 'react';
import { ChevronLeft, Search } from 'lucide-react';
import { motion } from 'framer-motion';
import RiskAccordion from '../RiskAccordion';
import type { AnalysisData } from '../../App';

interface AnalysisViewProps {
  analysis: AnalysisData | null;
  isLoading: boolean;
  onBack: () => void;
  onNewQuery: (query: string) => void;
}

const AnalysisView: React.FC<AnalysisViewProps> = ({ analysis, isLoading, onBack, onNewQuery }) => {
  const [inputQuery, setInputQuery] = useState('');
  const [showExplanation, setShowExplanation] = useState(false);

  React.useEffect(() => {
    setShowExplanation(false);
  }, [analysis?.query]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (inputQuery.trim()) {
      onNewQuery(inputQuery);
      setInputQuery('');
    }
  };

  const getAssetProfile = (rp: Record<string, any> | undefined, query: string) => {
    if (!rp) return null;
    return {
      assetId: rp.token_name || rp.token_symbol || query,
      type: rp.asset_type === 'native_asset' ? 'Native blockchain asset' : 'Smart contract token',
      address: rp.contract_address || 'N/A',
      marketCap: rp.market_cap ? `$${Number(rp.market_cap).toLocaleString()} (Rank #${rp.market_cap_rank || 'N/A'})` : 'N/A',
      exchanges: rp.exchanges_count ? `${rp.exchanges_count} platforms` : 'N/A'
    };
  };

  const profile = getAssetProfile(analysis?.risk_profile, analysis?.query || '');

  return (
    <motion.div
      key="analysis-view"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="flex-1 flex overflow-hidden"
    >
      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
         {/* Scrollable Main Area */}
        <div className="flex-1 overflow-y-auto" style={{ padding: '90px var(--space-4) var(--space-5)' }}>
          <div style={{ maxWidth: 720, margin: '0 auto', width: '100%' }}>
            
            {isLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 'var(--space-3)' }}>
                 <div
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: 'var(--radius)',
                      background: 'var(--accent)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Search size={24} color="white" className="spin" />
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)' }} className="pulse-dot">
                    Analyzing Security Signals...
                  </div>
              </div>
            ) : analysis ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {analysis.isError ? (
                  <div style={{ padding: 'var(--space-3)', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--red)', borderRadius: 'var(--radius)', color: 'var(--red)', fontWeight: 500 }}>
                    {analysis.response}
                  </div>
                ) : (
                  <div style={{ fontFamily: 'var(--font-sans)', lineHeight: 1.6 }}>
                    
                    {/* Title */}
                    <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text)', marginBottom: 'var(--space-6)', letterSpacing: '-0.02em' }}>
                      Risk Signal Report: <span style={{ color: 'var(--accent)' }}>{profile?.assetId || analysis.query}</span>
                    </div>

                    {/* 📋 Asset Profile */}
                    <div style={{ marginBottom: 'var(--space-4)' }}>
                      <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 20 }}>📋</span> Asset Profile
                      </div>
                      <div style={{ 
                        background: 'var(--bg-raised)', 
                        padding: 'var(--space-4)', 
                        borderRadius: 'var(--radius)',
                        border: '1px solid var(--border)',
                        boxShadow: '0 4px 15px rgba(0,0,0,0.1)'
                      }}>
                        {/* Table-like Profile Info */}
                        <div style={{ 
                          display: 'grid', 
                          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                          gap: 'var(--space-3)',
                          marginBottom: 'var(--space-4)',
                          paddingBottom: 'var(--space-4)',
                          borderBottom: '1px solid var(--border)'
                        }}>
                          <div>
                            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 4 }}>Asset ID</div>
                            <div style={{ fontSize: 14, fontWeight: 600 }}>{profile?.assetId}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 4 }}>Type</div>
                            <div style={{ fontSize: 14, fontWeight: 600 }}>{profile?.type}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 4 }}>Market Cap</div>
                            <div style={{ fontSize: 14, fontWeight: 600 }}>{profile?.marketCap}</div>
                          </div>
                          <div style={{ gridColumn: '1 / -1' }}>
                            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 4 }}>Contract Address</div>
                            <div style={{ fontSize: 13, fontFamily: 'monospace', background: 'var(--bg)', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--border)', wordBreak: 'break-all' }}>
                              {profile?.address}
                            </div>
                          </div>
                        </div>

                        {/* Factual Summary Paragraph (Extracted from Response) */}
                        <div style={{ marginTop: 'var(--space-3)' }}>
                          <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent)', marginBottom: 8, letterSpacing: '0.05em' }}>
                            Factual Summary
                          </div>
                          <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--text)', margin: 0, textAlign: 'justify' }}>
                            {(() => {
                              const summary = analysis.response.split(':::DETAILED_RISK_ANALYSIS:::')[0];
                              return summary
                                .replace(/###|---|#/g, '')
                                .replace(/[#*-]+/g, '')
                                .replace(/\n+/g, ' ')
                                .trim();
                            })()}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* 🔍 Detailed Risk Assessment */}
                    <div style={{ marginBottom: 'var(--space-4)' }}>
                      {analysis.risk_profile && (
                        <RiskAccordion 
                          data={analysis.risk_profile} 
                          onExplainRequest={() => setShowExplanation(!showExplanation)}
                          showExplanation={showExplanation}
                          explanationText={analysis.response}
                        />
                      )}
                    </div>

                    {/* 🔍 External Verification */}
                    <div style={{ marginBottom: 'var(--space-4)' }}>
                      <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 20 }}>🔍</span> External Verification
                      </div>
                      <div style={{ 
                        background: 'var(--bg-raised)', 
                        padding: 'var(--space-3)', 
                        borderRadius: 'var(--radius)',
                        border: '1px solid var(--border)' 
                      }}>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', fontSize: 14 }}>
                          <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Audit:</span>
                            <strong style={{ color: analysis.risk_profile?.is_audited ? 'var(--green)' : 'var(--text)' }}>
                              {analysis.risk_profile?.is_audited ? 'Audit Found' : 'No audit found'}
                            </strong>
                          </li>
                          <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Regulatory:</span>
                            <strong style={{ color: (analysis.risk_profile?.regulatory_warning_count || 0) > 0 ? 'var(--red)' : 'var(--green)' }}>
                              {(analysis.risk_profile?.regulatory_warning_count || 0) > 0 ? 'Warning detected' : 'No regulatory warnings found'}
                            </strong>
                          </li>
                        </ul>
                      </div>
                    </div>

                    <div style={{ marginTop: 'var(--space-5)', fontSize: 13, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        Source: 
                        <a 
                          href={analysis.risk_profile?.source_url || 'https://www.coingecko.com'} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={{ 
                            color: 'var(--accent)', 
                            textDecoration: 'none',
                            fontWeight: 600,
                            borderBottom: '1px solid transparent',
                            transition: 'border-color 0.2s'
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.borderBottomColor = 'var(--accent)')}
                          onMouseLeave={(e) => (e.currentTarget.style.borderBottomColor = 'transparent')}
                        >
                          {analysis.risk_profile?.source_url ? 
                            (analysis.risk_profile.source_url.includes('coingecko') ? 'CoinGecko' : 
                             analysis.risk_profile.source_url.includes('scan') ? 'Block Explorer' : 'Primary Data Source') 
                            : 'Primary Data Source'}
                        </a>
                      </div>
                      <div>Last Updated: {analysis.timestamp}</div>
                    </div>

                  </div>
                )}
              </motion.div>
            ) : null}
          </div>
        </div>

      </div>
    </motion.div>
  );
};

export default AnalysisView;

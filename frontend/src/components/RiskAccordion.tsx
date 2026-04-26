import React, { useState } from 'react';
import { SIGNAL_DEFINITIONS } from '../constants';
import { ChevronDown, ChevronUp, Shield, Info } from 'lucide-react';

interface RiskProfileProps {
  data: Record<string, any>;
  onExplainRequest?: () => void;
  showExplanation?: boolean;
  explanationText?: string;
}

type BadgeType = 'critical' | 'warning' | 'safe';

interface RiskItem {
  label: string;
  value: string;
  type: BadgeType;
  isRisk: boolean;
}

const RiskAccordion: React.FC<RiskProfileProps> = ({ data, onExplainRequest, showExplanation, explanationText }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  if (!data || Object.keys(data).length === 0) return null;

  const isHoneypot = data.is_honeypot === true;
  const isMintable = data.is_mintable === true;
  const isProxy = data.is_proxy === true;
  const isOpenSource = data.is_open_source === true;
  const isPausable = data.transfer_pausable === true;
  const cannotSellAll = data.cannot_sell_all === true;
  const buyTax = parseFloat(data.buy_tax || '0');
  const sellTax = parseFloat(data.sell_tax || '0');
  const creatorPercent = parseFloat(data.creator_percent || '0');
  const hasHighTax = buyTax > 0.1 || sellTax > 0.1;
  const hasHighConcentration = creatorPercent > 0.05;

  const items: RiskItem[] = [
    { label: 'Honeypot', value: isHoneypot ? 'Detected' : 'Clean', type: 'critical', isRisk: isHoneypot },
    { label: 'Source Code', value: isOpenSource ? 'Verified' : 'Unverified', type: 'safe', isRisk: !isOpenSource },
    { label: 'Buy Tax', value: `${(buyTax * 100).toFixed(1)}%`, type: 'critical', isRisk: hasHighTax },
    { label: 'Sell Tax', value: `${(sellTax * 100).toFixed(1)}%`, type: 'critical', isRisk: hasHighTax },
    { label: 'Pausable', value: isPausable ? 'Yes' : 'No', type: 'critical', isRisk: isPausable },
    { label: 'Proxy', value: isProxy ? 'Yes' : 'No', type: 'warning', isRisk: isProxy },
    { label: 'Creator %', value: `${(creatorPercent * 100).toFixed(1)}%`, type: 'warning', isRisk: hasHighConcentration },
    { label: 'Mintable', value: isMintable ? 'Active' : 'No', type: 'critical', isRisk: isMintable },
    { label: 'Sell Limit', value: cannotSellAll ? 'Restricted' : 'None', type: 'critical', isRisk: cannotSellAll },
  ];

  const getColor = (item: RiskItem) => {
    if (!item.isRisk) return 'var(--green)';
    if (item.type === 'critical') return 'var(--red)';
    return 'var(--yellow)';
  };

  return (
    <div
      className="glowing-card"
      style={{
        margin: '16px 0',
        borderRadius: 'var(--radius)',
        border: '1px solid var(--accent)',
        boxShadow: '0 0 10px var(--accent-muted)',
        position: 'relative',
        zIndex: isOpen ? 10 : 1
      }}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={!isOpen ? "glowing-card" : ""}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 18px',
          border: 'none',
          background: 'var(--bg-raised)',
          cursor: 'pointer',
          fontSize: 16,
          fontWeight: 700,
          color: 'var(--text)',
          fontFamily: 'var(--font-sans)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          borderRadius: isOpen ? 'var(--radius) var(--radius) 0 0' : 'var(--radius)',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--accent-muted)';
          e.currentTarget.style.boxShadow = '0 0 20px var(--accent-muted)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'var(--bg-raised)';
          e.currentTarget.style.boxShadow = 'none';
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Shield size={20} color="var(--accent)" />
          Detailed Risk Assessment
        </span>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          width: 28,
          height: 28,
          borderRadius: '50%',
          background: 'var(--accent-muted)',
          color: 'var(--accent)'
        }}>
          {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </div>
      </button>

      {isOpen && (
        <div style={{ padding: 'var(--space-3)', borderTop: '1px solid var(--border)', background: 'var(--bg)' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
              gap: 'var(--space-2)',
              marginBottom: onExplainRequest ? 'var(--space-4)' : 0
            }}
          >
            {items.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-raised)',
                  transition: 'transform 0.2s',
                  position: 'relative'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  setActiveTooltip(null);
                }}
              >
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: 'var(--text-secondary)',
                    marginBottom: 4,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  {item.label}
                  <button
                    onClick={() => setActiveTooltip(activeTooltip === item.label ? null : item.label)}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      cursor: 'help',
                      color: activeTooltip === item.label ? 'var(--accent)' : 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <Info size={12} />
                  </button>
                </div>

                {activeTooltip === item.label && (
                  <div
                    style={{
                      position: 'absolute',
                      bottom: 'calc(100% + 10px)',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      background: 'var(--bg-raised)',
                      border: '1px solid var(--accent)',
                      borderRadius: 4,
                      padding: '8px 12px',
                      fontSize: 11,
                      width: 180,
                      zIndex: 100,
                      boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                      color: 'var(--text)',
                      lineHeight: '1.4',
                      textAlign: 'center'
                    }}
                  >
                    {SIGNAL_DEFINITIONS[item.label] || "Signal definition pending."}
                    <div style={{
                      position: 'absolute',
                      top: '100%',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      borderWidth: 5,
                      borderStyle: 'solid',
                      borderColor: 'var(--accent) transparent transparent transparent'
                    }} />
                  </div>
                )}

                <div style={{ fontSize: 15, fontWeight: 700, color: getColor(item), display: 'flex', alignItems: 'center', gap: 4 }}>
                  {item.isRisk && <span style={{ width: 6, height: 6, borderRadius: '50%', background: getColor(item) }} />}
                  {item.value}
                </div>
              </div>
            ))}
          </div>
          {onExplainRequest && (
            <button
              onClick={onExplainRequest}
              className="glowing-card"
              style={{
                width: '100%',
                padding: '12px 16px',
                background: 'var(--accent)',
                border: 'none',
                borderRadius: 'var(--radius)',
                color: 'white',
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
                marginTop: 'var(--space-2)',
                boxShadow: '0 4px 12px var(--accent-muted)'
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.9')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
              {showExplanation ? 'Hide Risk Signal Explanation' : 'Explain These Risk Signals'}
            </button>
          )}

          {/* Detailed Risk Analysis Narrative Dropdown */}
          {showExplanation && explanationText && (
            <div style={{ 
              marginTop: 'var(--space-4)', 
              padding: 'var(--space-4)', 
              background: 'var(--bg-raised)', 
              border: '1px solid var(--border)', 
              borderRadius: 'var(--radius)',
              fontSize: 14,
              lineHeight: 1.7,
              color: 'var(--text)',
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.2)'
            }}>
              <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 'var(--space-3)', color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Shield size={18} /> Analysis Insights
              </div>
              
              {(() => {
                const parts = explanationText.split(':::DETAILED_RISK_ANALYSIS:::');
                const analysisPart = parts[1] || parts[0] || '';
                
                if (!analysisPart.trim()) return <p>No detailed analysis available for this asset.</p>;

                return (
                  <div style={{ color: 'var(--text-secondary)', textAlign: 'justify' }}>
                    {analysisPart
                      .replace(/###|---|#/g, '')
                      .replace(/\*\*/g, '')
                      .trim()}
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RiskAccordion;

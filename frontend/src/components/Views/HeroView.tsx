import React from 'react';
import { Search, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

interface HeroViewProps {
  query: string;
  setQuery: (q: string) => void;
  onVerify: () => void;
}

const HeroView: React.FC<HeroViewProps> = ({ query, setQuery, onVerify }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="flex-1 flex items-center justify-center"
      style={{ padding: 'var(--space-3)' }}
    >
      <div
        className="w-full"
        style={{ maxWidth: 'var(--max-w)' }}
      >
        {/* Heading */}
        <h1
          style={{
            fontSize: 40,
            fontWeight: 700,
            lineHeight: 1.15,
            letterSpacing: '-0.03em',
            color: 'var(--text)',
            marginBottom: 'var(--space-2)',
          }}
        >
          Verify any crypto asset.
        </h1>

        {/* Subheading */}
        <p
          style={{
            fontSize: 16,
            lineHeight: 1.5,
            color: 'var(--text-secondary)',
            marginBottom: 'var(--space-4)',
            maxWidth: 480,
          }}
        >
          Instant, on-chain risk analysis. No speculation — just deterministic signals.
        </p>

        {/* Search bar */}
        <div
          className="glowing-card"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-1)',
            background: 'var(--bg-raised)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            padding: 6,
            transition: 'border-color 0.2s',
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--accent)')}
          onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
        >
          <div style={{ paddingLeft: 8, color: 'var(--text-secondary)', display: 'flex' }}>
            <Search size={18} />
          </div>
          <input
            type="text"
            placeholder="Enter contract address or ticker…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onVerify()}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              background: 'transparent',
              fontSize: 14,
              fontWeight: 500,
              color: 'var(--text)',
              padding: '8px 4px',
              fontFamily: 'var(--font-sans)',
            }}
          />
          <button
            onClick={onVerify}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              border: 'none',
              borderRadius: 'calc(var(--radius) - 2px)',
              background: 'var(--accent)',
              color: 'white',
              fontSize: 13,
              fontWeight: 600,
              padding: '8px 16px',
              cursor: 'pointer',
              transition: 'opacity 0.2s',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.9')}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
          >
            Analyze
            <ArrowRight size={14} />
          </button>
        </div>

        {/* Data sources */}
        <div
          style={{
            display: 'flex',
            gap: 'var(--space-4)',
            marginTop: 'var(--space-5)',
            color: 'var(--text-secondary)',
            fontSize: 11,
            fontWeight: 500,
            letterSpacing: '0.04em',
            textTransform: 'uppercase' as const,
          }}
        >
          <div>
            <div style={{ color: 'var(--text-secondary)', opacity: 0.6, marginBottom: 2 }}>Security</div>
            <div style={{ color: 'var(--text)', fontWeight: 600 }}>GoPlus</div>
          </div>
          <div style={{ width: 1, background: 'var(--border)', alignSelf: 'stretch' }} />
          <div>
            <div style={{ color: 'var(--text-secondary)', opacity: 0.6, marginBottom: 2 }}>Market</div>
            <div style={{ color: 'var(--text)', fontWeight: 600 }}>CoinGecko</div>
          </div>
          <div style={{ width: 1, background: 'var(--border)', alignSelf: 'stretch' }} />
          <div>
            <div style={{ color: 'var(--text-secondary)', opacity: 0.6, marginBottom: 2 }}>Liquidity</div>
            <div style={{ color: 'var(--text)', fontWeight: 600 }}>DexTools</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default HeroView;

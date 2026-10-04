import React from 'react';

/**
 * Enterprise-grade ErrorBoundary
 * Catches unhandled runtime crashes in React tree, prevents white-screen of death,
 * and provides graceful recovery with state reset.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // Log to console for observability
    console.error('[React Doctor Sentinel] Uncaught component crash:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          background: '#0d0d0f',
          color: '#f0ede6',
          fontFamily: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
          textAlign: 'center',
        }}>
          <div style={{
            maxWidth: '520px',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '24px',
            padding: '36px 28px',
            backdropFilter: 'blur(20px)',
            boxShadow: '0 24px 64px rgba(0, 0, 0, 0.6)',
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '24px',
              margin: '0 auto 20px',
            }}>
              ⚠️
            </div>
            
            <h2 style={{ fontSize: '20px', fontWeight: '700', margin: '0 0 8px', letterSpacing: '-0.02em' }}>
              Storefront Encountered a Hiccup
            </h2>
            <p style={{ fontSize: '13px', color: '#9e9aa4', lineHeight: 1.6, margin: '0 0 24px' }}>
              An unexpected render fault was isolated safely by our Error Boundary without crashing your browser.
            </p>

            {this.state.error && (
              <pre style={{
                textAlign: 'left',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                padding: '12px',
                borderRadius: '10px',
                fontSize: '11px',
                color: '#f87171',
                overflowX: 'auto',
                marginBottom: '20px',
                maxHeight: '140px',
              }}>
                {this.state.error.toString()}
              </pre>
            )}

            <button
              onClick={this.handleReset}
              style={{
                background: '#f0ede6',
                color: '#0d0d0f',
                border: 'none',
                padding: '12px 28px',
                borderRadius: '12px',
                fontSize: '13px',
                fontWeight: '700',
                cursor: 'pointer',
                transition: 'transform 0.15s ease',
              }}
              onMouseOver={(e) => (e.currentTarget.style.transform = 'scale(1.02)')}
              onMouseOut={(e) => (e.currentTarget.style.transform = 'scale(1)')}
            >
              Reload & Restore Studio
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

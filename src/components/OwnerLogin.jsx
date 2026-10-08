import React, { useState } from 'react';
import Icon from './Icon.jsx';

export default function OwnerLogin({ onLogin, onPublicPreview, configured = true, error = '', busy = false }) {
  const [password, setPassword] = useState('');

  const submit = (event) => {
    event.preventDefault();
    onLogin(password);
  };

  return (
    <main className="owner-login-page">
      <div className="owner-login-card">
        <div className="owner-login-brand"><span className="brand-mark"><i /><i /><i /></span><span className="brand-name">shelf<span>.</span></span><span className="brand-beta">STUDIO</span></div>
        <h1>Creator Access</h1>
        <p>Manage your luxury catalog, live pricing, and verified affiliate drops.</p>
        <form onSubmit={submit} className="owner-login-form">
          <label className="field-label" htmlFor="owner-password">Studio Passcode</label>
          <input
            id="owner-password"
            type="password"
            className="input-text"
            placeholder="Enter passkey..."
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={busy || !configured}
            autoFocus
          />
          {error && <div className="owner-login-error"><Icon name="x" /><span>{error}</span></div>}
          <button type="submit" className="btn btn-primary btn-block" disabled={busy || !configured}>
            {busy ? 'Authenticating...' : 'Enter Studio'}
          </button>
        </form>
        {onPublicPreview && (
          <div className="owner-login-footer">
            <button type="button" className="btn-link" onClick={onPublicPreview}>
              Preview Public Storefront &rarr;
            </button>
          </div>
        )}
      </div>
    </main>
  );
}

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
        <div className="owner-login-art" aria-hidden="true"><span>✦</span><i /><b>YOUR<br />STYLE<br /><em>STUDIO</em></b></div>
        <p className="eyebrow">CREATOR ACCESS</p>
        <h1>Your little corner,<br /><em>behind the scenes.</em></h1>
        <p className="owner-login-copy">Sign in to curate, import and publish your product edits. Shoppers can browse your public page without an account.</p>
        <form className="owner-login-form" onSubmit={submit}>
          <label className="field-label" htmlFor="owner-password">Owner PIN / Passphrase</label>
          <input id="owner-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your private PIN or passphrase" required />
          {error && <p className="owner-login-error" role="alert">{error}</p>}
          <button className="button button-dark owner-login-submit" type="submit" disabled={busy || !password.trim()}>{busy ? 'Verifying…' : 'Unlock Private Studio'} <Icon name="arrowRight" size={16} /></button>
        </form>
        <button className="owner-public-link" type="button" onClick={onPublicPreview}><span>✦</span> Open the public shop preview <Icon name="arrowUpRight" size={14} /></button>
        <p className="owner-login-footnote"><Icon name="shield" size={13} /> Creator-only tools stay behind sign-in. Shopper pages are public.</p>
      </div>
    </main>
  );
}

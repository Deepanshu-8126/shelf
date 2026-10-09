import React, { useMemo, useState } from 'react';
import Icon from '../ui/Icon.jsx';

function lines(value) {
  return value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function statusLabel(status = '') {
  if (status === 'ready_update_existing') return 'Ready · update existing';
  if (status === 'ready_add_new') return 'Ready · new product';
  if (status.startsWith('published_update_existing')) return 'Published · updated';
  if (status.startsWith('published_new')) return 'Published · new product';
  if (status.startsWith('needs_')) return status.replaceAll('_', ' ');
  if (status.startsWith('not_published')) return status.replaceAll('_', ' ');
  return status.replaceAll('_', ' ') || 'Review needed';
}

export default function ImporterPanel({ onImportComplete, busy = false }) {
  const [pasteText, setPasteText] = useState('');
  const [report, setReport] = useState(null);
  const [publishing, setPublishing] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const count = useMemo(() => lines(pasteText).length, [pasteText]);

  const runAnalysis = async () => {
    if (!pasteText.trim()) return;
    setStatusMsg('Analyzing pasted links with Meesho creator parser...');
    try {
      const res = await fetch('/api/owner/import/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: pasteText }),
      });
      const data = await res.json();
      if (res.ok) {
        setReport(data);
        setStatusMsg(`Analysis ready · ${data.total_rows || 0} rows parsed`);
      } else {
        setStatusMsg(data.detail || 'Analysis error');
      }
    } catch (e) {
      setStatusMsg('Network error while analyzing.');
    }
  };

  const publishReady = async () => {
    if (!report) return;
    setPublishing(true);
    setStatusMsg('Publishing verified listings to catalog database...');
    try {
      const res = await fetch('/api/owner/import/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch_id: report.batch_id }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatusMsg(`Published · ${data.published_count || 0} listings live!`);
        if (onImportComplete) onImportComplete();
      } else {
        setStatusMsg(data.detail || 'Publishing error');
      }
    } catch {
      setStatusMsg('Network error while publishing.');
    } finally {
      setPublishing(false);
    }
  };

  return (
    <section className="importer-panel-card">
      <div className="importer-panel-header">
        <div>
          <h3>Creator Listing Batch Importer</h3>
          <p>Paste raw Meesho links, short links, or product URLs below.</p>
        </div>
      </div>
      <textarea
        className="importer-textarea"
        rows={6}
        placeholder="https://www.meesho.com/s/p/abc123&#10;https://www.meesho.com/item/p/xyz789"
        value={pasteText}
        onChange={(e) => setPasteText(e.target.value)}
      />
      <div className="importer-actions-row">
        <button
          type="button"
          className="btn btn-primary"
          onClick={runAnalysis}
          disabled={busy || !count}
        >
          <Icon name="sparkles" />
          <span>Analyze {count ? `(${count} links)` : ''}</span>
        </button>
        {report && (
          <button
            type="button"
            className="btn btn-success"
            onClick={publishReady}
            disabled={publishing}
          >
            <Icon name="check" />
            <span>Publish Verified Drops</span>
          </button>
        )}
      </div>
      {statusMsg && <div className="importer-status-pill">{statusMsg}</div>}
    </section>
  );
}

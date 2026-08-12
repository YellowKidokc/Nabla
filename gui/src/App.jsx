import React, { useMemo, useState } from 'react'

const TABS = ['Overview', 'Claims', 'Comparison', 'Raw']

function Badge({ children, tone = 'neutral' }) {
  return <span className={`badge ${tone}`}>{children}</span>
}

function Metric({ label, value }) {
  return <div className="metric"><span>{label}</span><strong>{value ?? '—'}</strong></div>
}

function extractStages(run) {
  if (!run) return []
  return run.stages || run.results || run.output || []
}

function downloadJson(name, value) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  URL.revokeObjectURL(url)
}

export default function App() {
  const [filename, setFilename] = useState('paper.md')
  const [text, setText] = useState('')
  const [provider, setProvider] = useState('deepseek')
  const [localOnly, setLocalOnly] = useState(false)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('Overview')
  const [humanStanding, setHumanStanding] = useState('UNREVIEWED')
  const [humanNotes, setHumanNotes] = useState('')

  const agreement = result?.comparison?.overall_agreement
  const band = result?.comparison?.agreement_band
  const sourceHash = result?.manifest?.source_sha256
  const localStages = useMemo(() => extractStages(result?.local_run), [result])
  const apiStages = useMemo(() => extractStages(result?.api_run), [result])

  async function readFile(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setFilename(file.name)
    setText(await file.text())
  }

  async function analyze() {
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, text, provider, local_only: localOnly })
      })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.error || 'Analysis refused')
      setResult(payload)
      setTab('Overview')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function loadGold() {
    setError('')
    try {
      const response = await fetch('/api/gold/master-equation')
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.error || 'Gold specimen unavailable')
      setResult({ status: 'gold_specimen', atlas_record: payload })
      setTab('Raw')
    } catch (err) {
      setError(err.message)
    }
  }

  function exportReview() {
    if (!result) return
    const receipt = {
      schema_version: 'atlas-human-review/v0.1',
      source_sha256: sourceHash || result?.atlas_record?.source?.content_hash || null,
      filename,
      standing: humanStanding,
      notes: humanNotes,
      compared_run: result?.run_dir || 'gold_specimen',
      generated_at: new Date().toISOString()
    }
    downloadJson(`${filename.replace(/\.[^.]+$/, '')}.human-review.json`, receipt)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">NABLA · CONSILIENCE ATLAS</div>
          <h1>Local Workbench</h1>
        </div>
        <div className="top-actions">
          <Badge tone="blue">Candidate sandbox</Badge>
          <button className="ghost" onClick={loadGold}>Load Gold-001</button>
        </div>
      </header>

      <main className="layout">
        <aside className="left-panel">
          <section>
            <h2>1 · Source</h2>
            <label className="file-drop">
              <input type="file" accept=".md,.txt,.html,.htm,.json" onChange={readFile} />
              <span>Choose paper</span>
              <small>{filename}</small>
            </label>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Paste a paper or load a Markdown/HTML/TXT file…"
            />
          </section>

          <section>
            <h2>2 · Lanes</h2>
            <label>Semantic provider
              <select value={provider} onChange={e => setProvider(e.target.value)} disabled={localOnly}>
                <option value="deepseek">DeepSeek</option>
                <option value="openai">OpenAI</option>
              </select>
            </label>
            <label className="check-row">
              <input type="checkbox" checked={localOnly} onChange={e => setLocalOnly(e.target.checked)} />
              Local NLP only — no external API
            </label>
            <button className="primary" onClick={analyze} disabled={busy || !text.trim()}>
              {busy ? 'Running rails…' : 'Analyze paper'}
            </button>
            <p className="hint">Both lanes receive the same frozen source and process contract. Comparison happens only after independent execution.</p>
          </section>

          <section>
            <h2>3 · Human ruling</h2>
            <label>Review state
              <select value={humanStanding} onChange={e => setHumanStanding(e.target.value)}>
                <option>UNREVIEWED</option>
                <option>ACCEPT_CANDIDATE</option>
                <option>NEEDS_CORRECTION</option>
                <option>RULE_AMBIGUITY</option>
                <option>REJECT</option>
              </select>
            </label>
            <textarea className="notes" value={humanNotes} onChange={e => setHumanNotes(e.target.value)} placeholder="Your notes / ruling…" />
            <button className="ghost full" onClick={exportReview} disabled={!result}>Export review receipt</button>
          </section>
        </aside>

        <section className="workspace">
          {error && <div className="error-box">{error}</div>}
          {!result && !error && (
            <div className="empty-state">
              <div className="periodic-icon">∇</div>
              <h2>Drop in a paper and run the rails.</h2>
              <p>The first version compares the local semantic lane against an external API lane, preserves receipts, and keeps your human review separate.</p>
            </div>
          )}

          {result && (
            <>
              <div className="summary-row">
                <Metric label="Run status" value={result.status} />
                <Metric label="Agreement" value={agreement == null ? '—' : Number(agreement).toFixed(3)} />
                <Metric label="Band" value={band} />
                <Metric label="Source hash" value={sourceHash ? sourceHash.slice(0, 12) : 'gold'} />
              </div>

              <nav className="tabs">
                {TABS.map(name => <button key={name} className={tab === name ? 'active' : ''} onClick={() => setTab(name)}>{name}</button>)}
              </nav>

              {tab === 'Overview' && (
                <div className="panel-grid">
                  <article className="panel">
                    <div className="panel-title"><h3>Local NLP lane</h3><Badge tone="cyan">independent</Badge></div>
                    <p>{result.local_run ? 'Completed and receipt preserved.' : 'Not available for this record.'}</p>
                    <div className="stage-list">
                      {Array.isArray(localStages) && localStages.slice(0, 8).map((s, i) => <div key={i} className="stage"><span>{i + 1}</span><code>{typeof s === 'string' ? s : (s.stage || s.name || s.status || 'stage')}</code></div>)}
                    </div>
                  </article>
                  <article className="panel">
                    <div className="panel-title"><h3>API lane</h3><Badge tone="purple">{provider}</Badge></div>
                    <p>{result.api_run ? 'Completed independently.' : localOnly ? 'Intentionally skipped.' : 'Not available.'}</p>
                    <div className="stage-list">
                      {Array.isArray(apiStages) && apiStages.slice(0, 8).map((s, i) => <div key={i} className="stage"><span>{i + 1}</span><code>{typeof s === 'string' ? s : (s.stage || s.name || s.status || 'stage')}</code></div>)}
                    </div>
                  </article>
                  <article className="panel wide">
                    <div className="panel-title"><h3>Convergence receipt</h3><Badge tone={band ? 'green' : 'neutral'}>{band || 'not compared'}</Badge></div>
                    <p className="big-copy">Agreement is a reproducibility signal only. It does not promote native grade, admit a bridge, or establish truth.</p>
                    <div className="receipt-line"><span>Run directory</span><code>{result.run_dir || 'gold specimen'}</code></div>
                  </article>
                </div>
              )}

              {tab === 'Claims' && (
                <div className="panel">
                  <h3>Claim / atom inspection</h3>
                  <p className="hint">This panel is intentionally conservative in v0.1. The next adapter will map stage outputs into AtlasRecord atom pills rather than inventing a second claim schema.</p>
                  <JsonPreview value={{ local: result.local_run, api: result.api_run }} />
                </div>
              )}

              {tab === 'Comparison' && (
                <div className="panel">
                  <div className="panel-title"><h3>Method comparison</h3><Badge tone="green">post-commit only</Badge></div>
                  {result.comparison ? <JsonPreview value={result.comparison} /> : <p>No comparison receipt exists for this run.</p>}
                </div>
              )}

              {tab === 'Raw' && (
                <div className="panel">
                  <div className="raw-toolbar"><h3>Canonical/raw receipt</h3><button className="ghost" onClick={() => downloadJson('atlas-workbench-result.json', result)}>Download JSON</button></div>
                  <JsonPreview value={result.atlas_record || result} />
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  )
}

function JsonPreview({ value }) {
  return <pre className="json-preview">{JSON.stringify(value, null, 2)}</pre>
}

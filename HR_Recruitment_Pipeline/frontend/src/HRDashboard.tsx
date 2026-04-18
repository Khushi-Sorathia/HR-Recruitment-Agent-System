import { useState, useEffect } from 'react';

interface Candidate {
  id: number;
  name: string;
  email: string;
  job_role: string;
  ats_score: number;
  total_score: number;
  pipeline_stage: string;
  created_at?: string;
  notes?: string;
}

const STAGES = [
  'All',
  'Resume Ingestion',
  'Technical Interview',
  'HR Screening',
  'Scheduling',
  'Scheduled',
  'Offer',
  'Rejected',
];

const ROLES = [
  'All',
  'Software Engineer',
  'Data Scientist',
  'Product Manager',
  'DevOps Engineer',
  'Frontend Developer',
  'Backend Developer',
];

function getBadgeClass(stage: string): string {
  switch (stage) {
    case 'Offer':
    case 'Scheduled':
      return 'badge-success';
    case 'Rejected':
      return 'badge-danger';
    case 'Technical Interview':
    case 'HR Screening':
    case 'Scheduling':
      return 'badge-pending';
    default:
      return 'badge-pending';
  }
}

export default function HRDashboard({ apiBase }: { apiBase: string }) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState('All');
  const [stageFilter, setStageFilter] = useState('All');

  // Chatbot State
  const [chatLog, setChatLog] = useState<{ sender: string; text: string }[]>([
    { sender: 'bot', text: 'Hello HR! I can query the recruitment pipeline for you. Try asking "How many candidates are in Technical Interview?" or "Move candidate Jane to Offer stage".' },
  ]);
  const [message, setMessage] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);

  // ─── Fetch Dashboard Data ──────────────────────────────────────────
  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (roleFilter !== 'All') params.append('role', roleFilter);
      if (stageFilter !== 'All') params.append('stage', stageFilter);

      const url = `${apiBase}/api/dashboard${params.toString() ? '?' + params.toString() : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch candidates');
      const data = await res.json();
      setCandidates(data);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [roleFilter, stageFilter]);

  // ─── Chatbot WebSocket ─────────────────────────────────────────────
  useEffect(() => {
    let isCancelled = false;
    const wsUrl = apiBase.replace('http', 'ws');
    const socket = new WebSocket(`${wsUrl}/api/ws/hr-chatbot`);
    socket.onmessage = (event) => {
      if (isCancelled) return;
      setChatLog((prev) => [...prev, { sender: 'bot', text: event.data }]);
      // Refresh dashboard after bot responds
      fetchCandidates();
    };
    socket.onerror = () => {
      if (isCancelled) return;
      setChatLog((prev) => [
        ...prev,
        { sender: 'bot', text: 'Connection error. Is the backend running?' },
      ]);
    };
    setWs(socket);
    return () => {
      isCancelled = true;
      socket.close();
    };
  }, []);

  const sendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setChatLog((prev) => [...prev, { sender: 'user', text: message }]);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(message);
    }
    setMessage('');
  };

  // ─── Stats ─────────────────────────────────────────────────────────
  const totalCandidates = candidates.length;
  const avgATS = totalCandidates > 0
    ? (candidates.reduce((sum, c) => sum + c.ats_score, 0) / totalCandidates).toFixed(1)
    : '0';
  const inPipeline = candidates.filter((c) => c.pipeline_stage !== 'Rejected').length;

  return (
    <div className="glass-panel">
      <h2 className="title">Talent Intelligence Dashboard</h2>

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{totalCandidates}</div>
          <div className="stat-label">Total Candidates</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{inPipeline}</div>
          <div className="stat-label">In Pipeline</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{avgATS}%</div>
          <div className="stat-label">Avg ATS Score</div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-row">
        <div className="filter-group">
          <label>Role</label>
          <select
            className="input-field filter-select"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <label>Stage</label>
          <select
            className="input-field filter-select"
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
          >
            {STAGES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <button className="btn-refresh" onClick={fetchCandidates}>
          <span style={{ fontSize: '1.2rem' }}>↻</span> Refresh Data
        </button>
      </div>

      {/* Candidates Table */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading candidates...
        </div>
      ) : candidates.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          No candidates found. Upload a resume through the Candidate Portal to get started.
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Candidate Details</th>
                <th>Role</th>
                <th>ATS Score</th>
                <th>Interview Score</th>
                <th>Current Stage</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div className="candidate-name">{c.name}</div>
                    <div className="candidate-email">{c.email}</div>
                  </td>
                  <td>{c.job_role}</td>
                  <td style={{ fontWeight: 500 }}>{c.ats_score.toFixed(0)}%</td>
                  <td style={{ fontWeight: 500, color: 'var(--primary)' }}>
                    {c.total_score > 0 ? c.total_score.toFixed(0) : '—'}
                  </td>
                  <td><span className={`badge ${getBadgeClass(c.pipeline_stage)}`}>{c.pipeline_stage}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Chatbot Window */}
      <div className="chatbot-area">
        <div className="chatbot-header">
          <div className="bot-avatar">AI</div>
          <h3>TalentAI Assistant</h3>
        </div>
        <div className="chatbot-messages">
          {chatLog.map((log, i) => (
            <div key={i} className={`msg ${log.sender === 'bot' ? 'msg-bot' : 'msg-user'}`}>
              {log.text}
            </div>
          ))}
        </div>
        <div className="chatbot-input-area">
          <form className="chatbot-input-form" onSubmit={sendChat}>
            <input
              id="chatbot-input"
              className="input-field"
              placeholder="Ask anything about candidates, stage changes, or scheduling..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <button id="chatbot-send" type="submit" className="btn-primary">
              Send
            </button>
          </form>
        </div>
      </div>

    </div>
  );
}

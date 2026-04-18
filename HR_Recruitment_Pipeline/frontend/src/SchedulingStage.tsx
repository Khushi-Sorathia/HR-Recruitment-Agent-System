import { useState } from 'react';

interface SchedulingStageProps {
  apiBase: string;
  candidateId: number;
  onComplete: () => void;
}

export default function SchedulingStage({ apiBase, candidateId, onComplete }: SchedulingStageProps) {
  const [availability, setAvailability] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    meeting_link: string;
    email_status: string;
  } | null>(null);
  const [error, setError] = useState('');

  const scheduleInterview = async () => {
    if (!availability.trim()) return;

    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${apiBase}/api/schedule/${candidateId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ availability }),
      });
      if (!res.ok) throw new Error('Failed to schedule interview.');
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <h2 className="title" style={{ color: 'var(--success)' }}>Interview Scheduled!</h2>
        <div className="meeting-card">
          <div className="meeting-icon">📅</div>
          <div className="meeting-details">
            <p><strong>Meeting Link:</strong></p>
            <a href={result.meeting_link} target="_blank" rel="noopener noreferrer" className="meeting-link">
              {result.meeting_link}
            </a>
          </div>
        </div>
        <div className="reasoning-box" style={{ marginTop: '1rem' }}>
          <h4>Email Status</h4>
          <p>{result.email_status}</p>
        </div>
        <button id="complete-btn" className="btn-primary" onClick={onComplete} style={{ marginTop: '1.5rem' }}>
          Complete Application
        </button>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 className="title">Schedule Your Interview</h2>
      <p style={{ marginBottom: '1.5rem', color: 'var(--text-muted)' }}>
        Please provide your available time slots so we can schedule a final interview with our team.
      </p>
      {error && <div className="error-banner">{error}</div>}
      <label className="question-label">Your Availability</label>
      <textarea
        id="availability-input"
        className="input-field"
        rows={3}
        placeholder="e.g., Monday to Friday, 10 AM – 4 PM IST, available from next week"
        value={availability}
        onChange={(e) => setAvailability(e.target.value)}
      />
      <button
        id="schedule-btn"
        className="btn-primary"
        onClick={scheduleInterview}
        disabled={loading || !availability.trim()}
      >
        {loading ? 'Scheduling...' : 'Schedule Interview'}
      </button>
    </div>
  );
}

import { useState } from 'react';

interface ScreeningStageProps {
  apiBase: string;
  candidateId: number;
  onComplete: () => void;
}

export default function ScreeningStage({ apiBase, candidateId, onComplete }: ScreeningStageProps) {
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState('');
  const [error, setError] = useState('');
  const [phase, setPhase] = useState<'load' | 'answer' | 'result'>('load');

  const fetchQuestions = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${apiBase}/api/screening/${candidateId}/questions`);
      if (!res.ok) throw new Error('Failed to fetch screening questions.');
      const data = await res.json();
      setQuestions(data.questions);
      setAnswers(new Array(data.questions.length).fill(''));
      setPhase('answer');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswers = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${apiBase}/api/screening/${candidateId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questions, answers }),
      });
      if (!res.ok) throw new Error('Failed to submit screening answers.');
      const data = await res.json();
      setEvaluation(data.evaluation);
      setPhase('result');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateAnswer = (index: number, value: string) => {
    setAnswers((prev) => {
      const updated = [...prev];
      updated[index] = value;
      return updated;
    });
  };

  // Phase: Load Questions
  if (phase === 'load') {
    return (
      <div className="glass-panel" style={{ maxWidth: '700px', margin: '0 auto', textAlign: 'center' }}>
        <h2 className="title">HR Screening</h2>
        <p style={{ marginBottom: '1.5rem', color: 'var(--text-muted)' }}>
          Our AI has analyzed your resume and prepared a few screening questions based on missing information.
        </p>
        {error && <div className="error-banner">{error}</div>}
        <button id="load-questions-btn" className="btn-primary" onClick={fetchQuestions} disabled={loading}>
          {loading ? 'Generating Questions...' : 'Start HR Screening'}
        </button>
      </div>
    );
  }

  // Phase: Answer Questions
  if (phase === 'answer') {
    return (
      <div className="glass-panel" style={{ maxWidth: '700px', margin: '0 auto' }}>
        <h2 className="title">HR Screening Questions</h2>
        <p style={{ marginBottom: '1.5rem', color: 'var(--text-muted)' }}>
          Please answer the following questions to help us understand your availability and fit.
        </p>
        {error && <div className="error-banner">{error}</div>}
        {questions.map((q, i) => (
          <div key={i} className="screening-question">
            <label className="question-label">
              {i + 1}. {q}
            </label>
            <textarea
              id={`screening-answer-${i}`}
              className="input-field"
              rows={2}
              placeholder="Your answer..."
              value={answers[i]}
              onChange={(e) => updateAnswer(i, e.target.value)}
            />
          </div>
        ))}
        <button
          id="submit-screening-btn"
          className="btn-primary"
          onClick={submitAnswers}
          disabled={loading || answers.some((a) => !a.trim())}
        >
          {loading ? 'Evaluating...' : 'Submit Screening Answers'}
        </button>
      </div>
    );
  }

  // Phase: Result
  return (
    <div className="glass-panel" style={{ maxWidth: '700px', margin: '0 auto' }}>
      <h2 className="title">Screening Complete</h2>
      <div className="reasoning-box">
        <h4>HR Evaluation</h4>
        <p>{evaluation}</p>
      </div>
      <button id="proceed-scheduling-btn" className="btn-primary" onClick={onComplete}>
        Proceed to Interview Scheduling
      </button>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import ScreeningStage from './ScreeningStage';
import SchedulingStage from './SchedulingStage';

interface CandidateData {
  id: number;
  name: string;
  email: string;
  job_role: string;
  ats_score: number;
  total_score: number;
  pipeline_stage: string;
  notes?: string;
}

interface ATSResult {
  score: number;
  reasoning: string;
  pass_screening: boolean;
}

interface InterviewDetail {
  question: string;
  score: number;
  reasoning: string;
}

type Step = 'upload' | 'ats_result' | 'interview' | 'screening' | 'scheduling' | 'done';

export default function CandidatePortal({ apiBase }: { apiBase: string }) {
  const [step, setStep] = useState<Step>('upload');
  const [candidate, setCandidate] = useState<CandidateData | null>(null);
  const [atsResult, setAtsResult] = useState<ATSResult | null>(null);

  // Upload State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('Software Engineer');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  // Interview State
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [timer, setTimer] = useState(30);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [interviewScore, setInterviewScore] = useState(0);
  const [interviewDetails, setInterviewDetails] = useState<InterviewDetail[]>([]);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(3);
  const timerRef = useRef<number | null>(null);

  // ─── Step 1: Resume Upload ─────────────────────────────────────────

  const submitResume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadError('');

    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('job_role', role);
    formData.append('file', file);

    try {
      const res = await fetch(`${apiBase}/api/upload-resume`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Upload failed');
      }

      const data = await res.json();
      setCandidate(data.candidate);
      setAtsResult(data.ats_result);
      setStep('ats_result');
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload resume. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  // ─── Step 2: ATS Result → Proceed or Rejected ─────────────────────

  const proceedToInterview = () => {
    setStep('interview');
  };

  // ─── Step 3: Technical Interview ───────────────────────────────────

  useEffect(() => {
    if (step === 'interview' && candidate && !ws) {
      const wsUrl = apiBase.replace('http', 'ws');
      const socket = new WebSocket(`${wsUrl}/api/ws/interview/${candidate.id}`);

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'question') {
          setQuestion(data.text);
          setTimer(data.timeout || 30);
          setAnswer('');
          setQuestionNumber(data.questionNumber || 0);
          setTotalQuestions(data.totalQuestions || 3);
        } else if (data.type === 'completion') {
          setInterviewComplete(true);
          setInterviewScore(data.score || 0);
          setInterviewDetails(data.details || []);
        } else if (data.type === 'error') {
          setUploadError(data.text);
        }
      };

      socket.onerror = () => {
        setUploadError('WebSocket connection failed. Is the backend running?');
      };

      setWs(socket);
      return () => socket.close();
    }
  }, [step, candidate]);

  useEffect(() => {
    if (step !== 'interview' || interviewComplete) return;

    if (timer > 0) {
      timerRef.current = window.setInterval(() => setTimer((t) => t - 1), 1000);
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    } else if (timer === 0) {
      submitAnswer();
    }
  }, [timer, interviewComplete, step]);

  const submitAnswer = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(answer || 'NO_ANSWER_TIMEOUT');
      setAnswer('');
    }
  };

  const handleCopyPaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    alert('Copy/Paste is disabled during the technical interview.');
  };

  const proceedToScreening = () => {
    setStep('screening');
  };

  const proceedToScheduling = () => {
    setStep('scheduling');
  };

  const onSchedulingDone = () => {
    setStep('done');
  };

  // ─── Render ────────────────────────────────────────────────────────

  // Step 1: Upload Form
  if (step === 'upload') {
    return (
      <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <h2 className="title">Candidate Application</h2>
        {uploadError && <div className="error-banner">{uploadError}</div>}
        <form onSubmit={submitResume}>
          <input
            id="name-input"
            className="input-field"
            placeholder="Full Name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            id="email-input"
            className="input-field"
            type="email"
            placeholder="Email Address"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <select
            id="role-select"
            className="input-field"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="Software Engineer">Software Engineer</option>
            <option value="Data Scientist">Data Scientist</option>
            <option value="Product Manager">Product Manager</option>
            <option value="DevOps Engineer">DevOps Engineer</option>
            <option value="Frontend Developer">Frontend Developer</option>
            <option value="Backend Developer">Backend Developer</option>
          </select>
          <input
            id="resume-upload"
            className="input-field"
            type="file"
            required
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <button id="submit-btn" type="submit" className="btn-primary" disabled={uploading}>
            {uploading ? 'Analyzing Resume...' : 'Submit Application'}
          </button>
        </form>
      </div>
    );
  }

  // Step 2: ATS Result
  if (step === 'ats_result' && atsResult) {
    return (
      <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <h2 className="title">Resume Analysis Result</h2>
        <div className="score-display">
          <div className={`score-circle ${atsResult.pass_screening ? 'score-pass' : 'score-fail'}`}>
            {atsResult.score.toFixed(0)}%
          </div>
          <p className="score-label">ATS Score</p>
        </div>
        <div className="reasoning-box">
          <h4>Analysis</h4>
          <p>{atsResult.reasoning}</p>
        </div>
        {atsResult.pass_screening ? (
          <div>
            <p className="status-pass">✓ You've passed the initial screening! Proceed to the technical interview.</p>
            <button id="proceed-interview-btn" className="btn-primary" onClick={proceedToInterview}>
              Start Technical Interview
            </button>
          </div>
        ) : (
          <div>
            <p className="status-fail">✗ Unfortunately, your resume did not meet the minimum threshold (80%) for this role.</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Consider updating your resume with more relevant skills and experience for the {candidate?.job_role} position.
            </p>
          </div>
        )}
      </div>
    );
  }

  // Step 3: Technical Interview
  if (step === 'interview') {
    return (
      <div className="glass-panel" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h2 className="title">Technical Interview</h2>
        {uploadError && <div className="error-banner">{uploadError}</div>}
        {interviewComplete ? (
          <div>
            <div className="score-display">
              <div className={`score-circle ${interviewScore >= 60 ? 'score-pass' : 'score-fail'}`}>
                {interviewScore.toFixed(0)}
              </div>
              <p className="score-label">Interview Score</p>
            </div>
            {interviewDetails.length > 0 && (
              <div className="interview-details">
                <h4>Question Breakdown</h4>
                {interviewDetails.map((d, i) => (
                  <div key={i} className="detail-card">
                    <p className="detail-question">Q{i + 1}: {d.question}</p>
                    <div className="detail-meta">
                      <span className="detail-score">Score: {d.score.toFixed(0)}/100</span>
                      <span className="detail-reasoning">{d.reasoning}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <button id="proceed-screening-btn" className="btn-primary" onClick={proceedToScreening}>
              Proceed to HR Screening
            </button>
          </div>
        ) : (
          <div>
            <div className="interview-header">
              <span className="question-counter">Question {questionNumber} of {totalQuestions}</span>
              <div className={`timer ${timer <= 10 ? 'timer-urgent' : ''}`}>
                00:{timer < 10 ? `0${timer}` : timer}
              </div>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${((totalQuestions - questionNumber) / totalQuestions) * 100}%` }}
              />
            </div>
            <p style={{ fontSize: '1.1rem', marginBottom: '1rem', lineHeight: '1.6' }}>{question}</p>
            <textarea
              id="answer-input"
              className="input-field"
              rows={5}
              placeholder="Type your answer here..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onCopy={handleCopyPaste}
              onPaste={handleCopyPaste}
              onCut={handleCopyPaste}
            />
            <button id="submit-answer-btn" className="btn-primary" onClick={submitAnswer}>
              Submit Answer
            </button>
          </div>
        )}
      </div>
    );
  }

  // Step 4: HR Screening
  if (step === 'screening' && candidate) {
    return (
      <ScreeningStage
        apiBase={apiBase}
        candidateId={candidate.id}
        onComplete={proceedToScheduling}
      />
    );
  }

  // Step 5: Scheduling
  if (step === 'scheduling' && candidate) {
    return (
      <SchedulingStage
        apiBase={apiBase}
        candidateId={candidate.id}
        onComplete={onSchedulingDone}
      />
    );
  }

  // Step 6: Done
  return (
    <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
      <h2 className="title" style={{ color: 'var(--success)' }}>🎉 Application Complete</h2>
      <p style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
        Thank you for completing the recruitment process! You should receive a confirmation email shortly.
      </p>
      <p style={{ color: 'var(--text-muted)' }}>
        Our HR team will be in touch regarding the next steps.
      </p>
    </div>
  );
}

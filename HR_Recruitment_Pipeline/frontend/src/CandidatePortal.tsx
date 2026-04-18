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
  const [isDragging, setIsDragging] = useState(false);

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

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  // ─── Step 2: ATS Result → Proceed or Rejected ─────────────────────

  const proceedToInterview = () => {
    setStep('interview');
  };

  // ─── Step 3: Technical Interview ───────────────────────────────────

  useEffect(() => {
    let isCancelled = false;
    if (step === 'interview' && candidate && !ws) {
      const wsUrl = apiBase.replace('http', 'ws');
      const socket = new WebSocket(`${wsUrl}/api/ws/interview/${candidate.id}`);

      socket.onmessage = (event) => {
        if (isCancelled) return;
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
        if (isCancelled) return;
        setUploadError('WebSocket connection failed. Is the backend running?');
      };

      setWs(socket);
      return () => {
        isCancelled = true;
        socket.close();
      };
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
      <div className="glass-panel" style={{ maxWidth: '650px', margin: '2rem auto' }}>
        <h2 className="title" style={{ textAlign: 'center' }}>Start Your Journey</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginBottom: '2rem' }}>
          Welcome to the automated recruitment pipeline. Upload your resume to begin.
        </p>

        {uploadError && <div className="error-banner">{uploadError}</div>}
        
        <form onSubmit={submitResume}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
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
          </div>
          
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
          
          <div 
            className={`upload-area ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('resume-upload')?.click()}
          >
            <div className="upload-icon">📄</div>
            <div className="upload-text">
              {file ? file.name : 'Drag & drop your resume here'}
            </div>
            <div className="upload-subtext">
              {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'or click to browse (.pdf only)'}
            </div>
            <input
              id="resume-upload"
              type="file"
              style={{ display: 'none' }}
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </div>
          
          <button id="submit-btn" type="submit" className="btn-primary" disabled={uploading || !file}>
            {uploading ? 'Analyzing Resume...' : 'Submit Application'}
          </button>
        </form>
      </div>
    );
  }

  // Step 2: ATS Result
  if (step === 'ats_result' && atsResult) {
    return (
      <div className="glass-panel" style={{ maxWidth: '600px', margin: '2rem auto', textAlign: 'center' }}>
        <h2 className="title">Resume Analysis Complete</h2>
        <div className="score-display">
          <div className={`score-circle ${atsResult.pass_screening ? 'score-pass' : 'score-fail'}`}>
            {atsResult.score.toFixed(0)}%
          </div>
          <p className="score-label">Intelligent ATS Score</p>
        </div>
        
        <div style={{ background: 'var(--bg-surface-low)', padding: '1.5rem', borderRadius: '16px', marginBottom: '2rem', textAlign: 'left', border: '1px solid var(--ghost-border)' }}>
          <h4 style={{ margin: '0 0 0.5rem', color: 'var(--primary)', fontWeight: 600 }}>AI Feedback</h4>
          <p style={{ margin: 0, color: 'var(--text-main)', lineHeight: 1.6 }}>{atsResult.reasoning}</p>
        </div>

        {atsResult.pass_screening ? (
          <div>
            <p className="status-pass" style={{ color: 'var(--success)', fontWeight: 600, fontSize: '1.1rem', marginBottom: '1.5rem' }}>
              ✓ You've passed the initial screening! Proceed to the technical interview.
            </p>
            <button id="proceed-interview-btn" className="btn-primary" onClick={proceedToInterview}>
              Begin Technical Interview
            </button>
          </div>
        ) : (
          <div>
            <p className="status-fail" style={{ color: 'var(--danger)', fontWeight: 600, fontSize: '1.1rem', marginBottom: '1rem' }}>
              ✗ Unfortunately, your resume did not meet the minimum threshold (80%) for this role.
            </p>
            <p style={{ color: 'var(--text-muted)' }}>
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
      <div className="glass-panel" style={{ maxWidth: '800px', margin: '2rem auto' }}>
        <h2 className="title">Technical Interview</h2>
        {uploadError && <div className="error-banner">{uploadError}</div>}
        {interviewComplete ? (
          <div style={{ textAlign: 'center' }}>
            <div className="score-display">
              <div className={`score-circle ${interviewScore >= 60 ? 'score-pass' : 'score-fail'}`}>
                {interviewScore.toFixed(0)}
              </div>
              <p className="score-label">Interview Score</p>
            </div>
            {interviewDetails.length > 0 && (
              <div className="interview-details" style={{ textAlign: 'left', marginTop: '2rem' }}>
                <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Question Breakdown</h4>
                {interviewDetails.map((d, i) => (
                  <div key={i} style={{ background: 'var(--bg-surface-low)', padding: '1.5rem', borderRadius: '16px', marginBottom: '1rem', border: '1px solid var(--ghost-border)' }}>
                    <p style={{ margin: '0 0 0.5rem', fontWeight: 600, color: '#fff' }}>Q{i + 1}: {d.question}</p>
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '0.8rem', fontSize: '0.9rem' }}>
                      <span style={{ fontWeight: 600, color: 'var(--primary)' }}>Score: {d.score.toFixed(0)}/100</span>
                      <span style={{ color: 'var(--text-muted)' }}>{d.reasoning}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <button id="proceed-screening-btn" className="btn-primary" style={{ marginTop: '2rem' }} onClick={proceedToScreening}>
              Proceed to HR Screening
            </button>
          </div>
        ) : (
          <div>
            <div className="interview-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <span style={{ fontWeight: 600, color: 'var(--primary)' }}>Question {questionNumber} of {totalQuestions}</span>
              <div className={`timer ${timer <= 10 ? 'timer-urgent' : ''}`} style={{ fontSize: '1.5rem', fontWeight: 700, color: timer <= 10 ? 'var(--danger)' : 'var(--text-main)' }}>
                00:{timer < 10 ? `0${timer}` : timer}
              </div>
            </div>
            
            <div style={{ width: '100%', height: '6px', background: 'var(--bg-surface-low)', borderRadius: '3px', overflow: 'hidden', marginBottom: '2rem' }}>
              <div
                style={{ height: '100%', background: 'linear-gradient(90deg, var(--primary), var(--success))', width: `${((totalQuestions - questionNumber) / totalQuestions) * 100}%`, transition: 'width 0.5s ease' }}
              />
            </div>
            
            <p style={{ fontSize: '1.2rem', marginBottom: '1.5rem', lineHeight: '1.6', color: '#fff' }}>{question}</p>
            
            <textarea
              id="answer-input"
              className="input-field"
              rows={6}
              style={{ background: 'var(--bg-base)' }}
              placeholder="Type your answer here..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onCopy={handleCopyPaste}
              onPaste={handleCopyPaste}
              onCut={handleCopyPaste}
            />
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button id="submit-answer-btn" className="btn-primary" style={{ width: 'auto', padding: '0.75rem 2rem' }} onClick={submitAnswer}>
                Submit Answer
              </button>
            </div>
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
    <div className="glass-panel" style={{ maxWidth: '600px', margin: '2rem auto', textAlign: 'center' }}>
      <h2 className="title" style={{ color: 'var(--success)' }}>🎉 Application Complete</h2>
      <p style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#fff' }}>
        Thank you for completing the recruitment process! You should receive a confirmation email shortly.
      </p>
      <p style={{ color: 'var(--text-muted)' }}>
        Our HR team will be in touch regarding the next steps.
      </p>
    </div>
  );
}

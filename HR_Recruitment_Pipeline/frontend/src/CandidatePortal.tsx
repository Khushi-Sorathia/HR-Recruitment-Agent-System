import { useState, useEffect } from 'react';

export default function CandidatePortal() {
  const [step, setStep] = useState<'upload' | 'interview'>('upload');
  const [candidateId, setCandidateId] = useState<number | null>(null);
  
  // Upload State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('Software Engineer');
  // Interview State
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [timer, setTimer] = useState(30);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [score, setScore] = useState('');

  const submitResume = async (e: any) => {
    e.preventDefault();
    // Normally upload file to FastAPI, mock here
    setCandidateId(123);
    setStep('interview');
  };

  useEffect(() => {
    if (step === 'interview' && candidateId && !ws) {
      const socket = new WebSocket(`ws://localhost:8000/api/ws/interview/${candidateId}`);
      
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'question') {
          setQuestion(data.text);
          setTimer(data.timeout || 30);
          setAnswer('');
        } else if (data.type === 'completion') {
          setInterviewComplete(true);
          setScore(data.text);
        }
      };
      setWs(socket);
      return () => socket.close();
    }
  }, [step, candidateId, ws]);

  useEffect(() => {
    if (timer > 0 && !interviewComplete) {
      const interval = setInterval(() => setTimer((t) => t - 1), 1000);
      return () => clearInterval(interval);
    } else if (timer === 0 && !interviewComplete) {
      submitAnswer(); // Auto submit on timeout
    }
  }, [timer, interviewComplete]);

  const submitAnswer = () => {
    if (ws) {
      ws.send(answer || "NO_ANSWER_TIMEOUT");
    }
  };

  const handleCopyPaste = (e: any) => {
    e.preventDefault();
    alert("Copy/Paste is disabled during the technical interview.");
  };

  if (step === 'upload') {
    return (
      <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <h2 className="title">Candidate Application</h2>
        <form onSubmit={submitResume}>
          <input className="input-field" placeholder="Full Name" required value={name} onChange={e => setName(e.target.value)} />
          <input className="input-field" type="email" placeholder="Email Address" required value={email} onChange={e => setEmail(e.target.value)} />
          <select className="input-field" value={role} onChange={e => setRole(e.target.value)}>
            <option value="Software Engineer">Software Engineer</option>
            <option value="Data Scientist">Data Scientist</option>
            <option value="Product Manager">Product Manager</option>
          </select>
          <input className="input-field" type="file" required accept=".pdf" />
          <button type="submit" className="btn-primary">Submit Application</button>
        </form>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2 className="title">Technical Interview</h2>
      {interviewComplete ? (
        <div style={{ textAlign: 'center' }}>
          <h3 style={{ color: 'var(--success)' }}>{score}</h3>
          <p>Thank you. AI HR will reach out for the screening stage.</p>
        </div>
      ) : (
        <div>
          <div className="timer">00:{timer < 10 ? `0${timer}` : timer}</div>
          <p style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>{question}</p>
          <textarea 
            className="input-field" 
            rows={5} 
            placeholder="Type your answer here..."
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            onCopy={handleCopyPaste}
            onPaste={handleCopyPaste}
            onCut={handleCopyPaste}
          />
          <button className="btn-primary" onClick={submitAnswer}>Submit Answer</button>
        </div>
      )}
    </div>
  );
}

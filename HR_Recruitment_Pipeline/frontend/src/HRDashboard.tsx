import { useState, useEffect } from 'react';

export default function HRDashboard() {
  const [chatLog, setChatLog] = useState<{sender: string, text: string}[]>([
    { sender: 'bot', text: 'Hello HR! How can I assist you with the recruitment pipeline today?' }
  ]);
  const [message, setMessage] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/api/ws/hr-chatbot');
    socket.onmessage = (event) => {
      setChatLog(prev => [...prev, { sender: 'bot', text: event.data }]);
    };
    setWs(socket);
    return () => socket.close();
  }, []);

  const sendChat = (e: any) => {
    e.preventDefault();
    if (!message) return;
    setChatLog(prev => [...prev, { sender: 'user', text: message }]);
    if (ws) ws.send(message);
    setMessage('');
  };

  return (
    <div className="glass-panel">
      <h2 className="title">Recruitment Pipeline</h2>
      
      <table className="table">
        <thead>
          <tr>
            <th>Candidate</th>
            <th>Role</th>
            <th>ATS Score</th>
            <th>Stage</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Jane Doe</td>
            <td>Software Engineer</td>
            <td>85%</td>
            <td><span className="badge badge-success">Technical Interview</span></td>
          </tr>
          <tr>
            <td>John Smith</td>
            <td>Data Scientist</td>
            <td>78%</td>
            <td><span className="badge badge-danger">Rejected</span></td>
          </tr>
        </tbody>
      </table>

      <div className="chatbot-area">
        <h3>HR Chatbot (AI)</h3>
        <div className="chatbot-messages">
          {chatLog.map((log, i) => (
            <div key={i} className={`msg ${log.sender === 'bot' ? 'msg-bot' : 'msg-user'}`}>
              {log.text}
            </div>
          ))}
        </div>
        <form onSubmit={sendChat} style={{ display: 'flex', gap: '1rem' }}>
          <input className="input-field" style={{ marginBottom: 0 }} placeholder="Query candidates or change stages..." value={message} onChange={e => setMessage(e.target.value)} />
          <button type="submit" className="btn-primary" style={{ width: 'auto' }}>Send</button>
        </form>
      </div>
    </div>
  );
}

import { useState } from 'react';
import CandidatePortal from './CandidatePortal';
import HRDashboard from './HRDashboard';
import './index.css';

function App() {
  const [view, setView] = useState<'candidate' | 'hr'>('candidate');

  return (
    <div className="app-container">
      <header className="header">
        <div className="brand">AI Recruitment Pipeline</div>
        <nav className="nav-buttons">
          <button 
            className={view === 'candidate' ? 'active' : ''} 
            onClick={() => setView('candidate')}
          >
            Candidate Portal
          </button>
          <button 
            className={view === 'hr' ? 'active' : ''} 
            onClick={() => setView('hr')}
          >
            HR Dashboard
          </button>
        </nav>
      </header>
      
      <main>
        {view === 'candidate' ? <CandidatePortal /> : <HRDashboard />}
      </main>
    </div>
  );
}

export default App;

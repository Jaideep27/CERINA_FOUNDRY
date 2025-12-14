import { useState, useEffect } from 'react';
import { AgentTerminal } from './components/AgentTerminal';
import { ProtocolEditor } from './components/ProtocolEditor';
import { InputPanel } from './components/InputPanel';
import { Shield } from 'lucide-react';

function App() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [artifact, setArtifact] = useState('');
  const [isPaused, setIsPaused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showResumePrompt, setShowResumePrompt] = useState(false);
  const [savedThreadId, setSavedThreadId] = useState<string | null>(null);
  const [savedQuery, setSavedQuery] = useState<string>('');

  // Check for interrupted threads on load
  useEffect(() => {
    const checkInterruptedThread = async () => {
      const storedThreadId = localStorage.getItem('active_thread_id');
      const storedQuery = localStorage.getItem('active_query');

      if (storedThreadId) {
        try {
          const res = await fetch(`http://127.0.0.1:8000/check_thread/${storedThreadId}`);
          const data = await res.json();

          if (data.exists && !data.completed) {
            // Thread exists and is incomplete - offer to resume
            setSavedThreadId(storedThreadId);
            setSavedQuery(storedQuery || '');
            setShowResumePrompt(true);
          } else {
            // Thread completed or doesn't exist - clear storage
            localStorage.removeItem('active_thread_id');
            localStorage.removeItem('active_query');
          }
        } catch (err) {
          console.error('Error checking interrupted thread:', err);
          localStorage.removeItem('active_thread_id');
          localStorage.removeItem('active_query');
        }
      }
    };

    checkInterruptedThread();
  }, []);

  const startTask = async (query: string) => {
    setLoading(true);
    setArtifact('');
    setIsPaused(false);
    setShowResumePrompt(false);
    try {
      const res = await fetch('http://127.0.0.1:8000/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      setThreadId(data.thread_id);

      // Save to localStorage for resume capability
      localStorage.setItem('active_thread_id', data.thread_id);
      localStorage.setItem('active_query', query);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const approveTask = async (id: string) => {
    try {
      await fetch('http://127.0.0.1:8000/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: id })
      });
      setIsPaused(false);
    } catch (err) {
      console.error(err);
    }
  };

  const requestRevision = async (id: string, feedback: string) => {
    setIsPaused(false);
    try {
      await fetch('http://127.0.0.1:8000/revise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: id, feedback })
      });
    } catch (err) {
      console.error(err);
    }
  };

  const handleResume = async () => {
    if (!savedThreadId) return;

    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: savedThreadId })
      });
      const data = await res.json();

      if (data.status === 'Resumed') {
        setThreadId(savedThreadId);
        setShowResumePrompt(false);
      } else if (data.status === 'Already completed') {
        alert('This workflow has already completed.');
        localStorage.removeItem('active_thread_id');
        localStorage.removeItem('active_query');
        setShowResumePrompt(false);
      }
    } catch (err) {
      console.error('Error resuming:', err);
      alert('Failed to resume workflow.');
    } finally {
      setLoading(false);
    }
  };

  const handleDiscard = () => {
    localStorage.removeItem('active_thread_id');
    localStorage.removeItem('active_query');
    setShowResumePrompt(false);
    setSavedThreadId(null);
  };

  const handleStateUpdate = (state: any) => {
    if (state.artifact) {
      setArtifact(state.artifact);
    }
    // Check for paused state - _controlContent contains "Interrupted" from backend
    if (state.status === "Waiting for Approval" || state._controlContent === "Interrupted") {
      setIsPaused(true);
    }

    // Clear localStorage when workflow completes or is rejected
    if (state.status === "Rejected" || state._controlContent === "Finished") {
      localStorage.removeItem('active_thread_id');
      localStorage.removeItem('active_query');
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col font-sans">
      {/* Resume Prompt Banner */}
      {showResumePrompt && (
        <div className="bg-yellow-50 border-b-2 border-yellow-400 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-semibold text-gray-800">Interrupted Workflow Detected</p>
              <p className="text-sm text-gray-600">
                Query: "{savedQuery || 'Unknown'}" - Would you like to resume?
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleResume}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
            >
              ▶️ Resume
            </button>
            <button
              onClick={handleDiscard}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 font-medium"
            >
              ✕ Discard
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-3 shadow-sm z-10">
        <div className="bg-blue-600 p-2 rounded-lg text-white">
          <Shield size={24} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-900 tracking-tight">CERINA FOUNDRY</h1>
          <p className="text-xs text-gray-500 font-medium">AGENTIC PROTOCOL SYNTHESIS ENGINE</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 grid grid-cols-12 gap-6 h-[calc(100vh-80px)]">

        {/* Left Col: Terminal & Input */}
        <div className="col-span-4 flex flex-col gap-6 h-full">
          <InputPanel onStart={startTask} isLoading={loading} />
          <div className="flex-1 min-h-0">
            <AgentTerminal threadId={threadId} onStateUpdate={handleStateUpdate} />
          </div>
        </div>

        {/* Right Col: Editor */}
        <div className="col-span-8 h-full">
          <ProtocolEditor
            artifact={artifact}
            isPaused={isPaused}
            threadId={threadId}
            onApprove={approveTask}
            onRequestRevision={requestRevision}
          />
        </div>

      </main>
    </div>
  );
}

export default App;

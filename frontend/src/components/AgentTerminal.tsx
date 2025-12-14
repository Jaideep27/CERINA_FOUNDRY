import { useEffect, useState, useRef } from 'react';
import { Terminal } from 'lucide-react';

interface Log {
    type: 'status' | 'agent_start' | 'agent_output' | 'agent_end' | 'control' | 'error';
    agent?: string;
    content: string;
    state?: any;
}

interface AgentTerminalProps {
    threadId: string | null;
    onStateUpdate: (state: any) => void;
}

const AGENT_ICONS: Record<string, string> = {
    System: '🚀',
    Filter: '🔍',
    Drafter: '📝',
    Safety: '🛡️',
    Critic: '🎯',
    Interrupt: '⏸️',
    Rejection: '❌',
};

const AGENT_COLORS: Record<string, string> = {
    System: 'text-blue-400',
    Filter: 'text-purple-400',
    Drafter: 'text-green-400',
    Safety: 'text-yellow-400',
    Critic: 'text-orange-400',
    Interrupt: 'text-cyan-400',
    Rejection: 'text-red-400',
};

export function AgentTerminal({ threadId, onStateUpdate }: AgentTerminalProps) {
    const [logs, setLogs] = useState<Log[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!threadId) return;

        let reconnectAttempts = 0;
        const maxReconnects = 5;
        let eventSource: EventSource | null = null;

        const connectEventSource = () => {
            eventSource = new EventSource(`http://127.0.0.1:8000/stream/${threadId}`);

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setLogs(prev => [...prev, data]);

                    if (data.type === 'control' && data.state) {
                        // Include the content field so App can detect "Interrupted"
                        onStateUpdate({ ...data.state, _controlContent: data.content });
                    }

                    // Reset reconnect attempts on successful message
                    reconnectAttempts = 0;
                } catch (e) {
                    console.error("Parse error", e);
                }
            };

            eventSource.onerror = () => {
                eventSource?.close();

                if (reconnectAttempts < maxReconnects) {
                    reconnectAttempts++;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 10000); // Exponential backoff

                    setLogs(prev => [...prev, {
                        type: 'status',
                        agent: 'System',
                        content: `🔄 Connection lost. Reconnecting (${reconnectAttempts}/${maxReconnects})...`
                    }]);

                    setTimeout(() => {
                        connectEventSource(); // Retry connection
                    }, delay);
                } else {
                    setLogs(prev => [...prev, {
                        type: 'error',
                        content: 'Connection closed. Max reconnection attempts reached.'
                    }]);
                }
            };
        };

        connectEventSource();

        return () => {
            eventSource?.close();
        };
    }, [threadId]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    const renderLog = (log: Log, index: number) => {
        const icon = log.agent ? AGENT_ICONS[log.agent] || '⚙️' : '📋';
        const colorClass = log.agent ? AGENT_COLORS[log.agent] || 'text-gray-400' : 'text-gray-400';

        if (log.type === 'agent_start') {
            return (
                <div key={index} className={`flex items-start gap-2 py-2 border-l-2 border-l-gray-700 pl-3 ${colorClass}`}>
                    <span className="text-lg">{icon}</span>
                    <div>
                        <span className="font-bold">{log.agent} Agent</span>
                        <span className="text-gray-500 ml-2">• {log.content}</span>
                    </div>
                </div>
            );
        }

        if (log.type === 'agent_output') {
            return (
                <div key={index} className="ml-8 my-1 p-2 bg-gray-900 rounded text-sm text-gray-300 font-mono whitespace-pre-wrap">
                    {log.content}
                </div>
            );
        }

        if (log.type === 'agent_end') {
            return (
                <div key={index} className="ml-8 text-xs text-gray-500 mb-2">
                    ✓ {log.agent} completed
                </div>
            );
        }

        if (log.type === 'status') {
            return (
                <div key={index} className={`flex items-center gap-2 py-1 ${colorClass}`}>
                    <span>{icon}</span>
                    <span className="font-semibold">{log.content}</span>
                </div>
            );
        }

        if (log.type === 'control') {
            return (
                <div key={index} className="py-2 px-3 my-2 bg-blue-900/30 border border-blue-700 rounded text-blue-300">
                    <span className="font-bold">⏸️ {log.content}</span>
                    {log.content === 'Interrupted' && <span className="ml-2 text-sm">• Awaiting approval</span>}
                </div>
            );
        }

        if (log.type === 'error') {
            return (
                <div key={index} className="py-1 text-red-500">
                    ❌ {log.content}
                </div>
            );
        }

        return null;
    };

    return (
        <div className="flex flex-col h-full bg-black text-green-400 font-mono p-4 rounded-lg border border-gray-800 shadow-2xl">
            <div className="flex items-center gap-2 mb-3 border-b border-gray-800 pb-2">
                <Terminal size={18} />
                <span className="text-sm font-bold tracking-wider">CERINA OS v1.0 // AGENT EXECUTION</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1" ref={scrollRef}>
                {logs.length === 0 && <span className="opacity-50">System Standby...</span>}
                {logs.map((log, i) => renderLog(log, i))}
            </div>
        </div>
    );
}

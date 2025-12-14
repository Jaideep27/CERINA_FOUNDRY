import { useState } from 'react';
import { Send, Play, Loader2 } from 'lucide-react';

interface InputPanelProps {
    onStart: (query: string) => void;
    isLoading: boolean;
}

export function InputPanel({ onStart, isLoading }: InputPanelProps) {
    const [query, setQuery] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim() && !isLoading) {
            onStart(query);
        }
    };

    return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
            <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Describe the CBT protocol needed (e.g., 'Exposure hierarchy for social anxiety')..."
                    className="flex-1 p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none text-gray-800 placeholder-gray-400"
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    disabled={isLoading}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                    {isLoading ? <Loader2 className="animate-spin" /> : <Play size={18} />}
                    Start Foundry
                </button>
            </form>
        </div>
    );
}

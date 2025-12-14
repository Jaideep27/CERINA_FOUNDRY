import { useState, useEffect } from 'react';
import { CheckCircle, FileText, MessageSquare, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ProtocolEditorProps {
    artifact: string;
    isPaused: boolean;
    threadId: string | null;
    onApprove: (threadId: string, feedback?: string) => void;
    onRequestRevision: (threadId: string, feedback: string) => void;
}

export function ProtocolEditor({ artifact, isPaused, threadId, onApprove, onRequestRevision }: ProtocolEditorProps) {
    const [content, setContent] = useState(artifact);
    const [feedback, setFeedback] = useState('');
    const [showFeedback, setShowFeedback] = useState(false);

    useEffect(() => {
        setContent(artifact);
    }, [artifact]);

    const handleApprove = () => {
        if (threadId) {
            onApprove(threadId);
            setFeedback('');
            setShowFeedback(false);
        }
    };

    const handleRequestRevision = () => {
        if (threadId && feedback.trim()) {
            onRequestRevision(threadId, feedback.trim());
            setFeedback('');
            setShowFeedback(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white text-gray-900 rounded-lg shadow-lg border border-gray-200">
            <div className="flex justify-between items-center p-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center gap-2">
                    <FileText className="text-gray-500" />
                    <span className="font-semibold text-gray-700">Protocol Draft</span>
                </div>
                <div className="flex gap-2">
                    {isPaused && (
                        <>
                            <button
                                onClick={() => setShowFeedback(!showFeedback)}
                                className={`flex items-center gap-2 px-4 py-2 rounded shadow transition-all ${showFeedback
                                    ? 'bg-orange-600 text-white'
                                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                                    }`}
                            >
                                <MessageSquare size={16} /> Provide Feedback
                            </button>
                            <button
                                onClick={handleApprove}
                                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded shadow transition-all"
                            >
                                <CheckCircle size={16} /> Approve & Finalize
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Feedback Panel */}
            {showFeedback && isPaused && (
                <div className="p-4 bg-orange-50 border-b border-orange-200">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Your Feedback (The agents will revise based on this)
                    </label>
                    <textarea
                        className="w-full p-3 border border-orange-300 rounded focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                        rows={3}
                        placeholder="e.g., 'I don't like step 3' or 'Add more examples for breathing exercises' or 'Make it shorter'"
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                    />
                    <button
                        onClick={handleRequestRevision}
                        disabled={!feedback.trim()}
                        className={`mt-2 flex items-center gap-2 px-4 py-2 rounded shadow transition-all ${feedback.trim()
                            ? 'bg-orange-600 hover:bg-orange-700 text-white'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            }`}
                    >
                        <RefreshCw size={16} /> Request Revision
                    </button>
                </div>
            )}

            <div className="flex-1 p-6 overflow-y-auto">
                <div className="prose prose-slate max-w-none
                    prose-headings:text-gray-900
                    prose-h1:text-3xl prose-h1:font-bold prose-h1:mb-6 prose-h1:mt-8 prose-h1:border-b-2 prose-h1:border-blue-300 prose-h1:pb-3
                    prose-h2:text-2xl prose-h2:font-semibold prose-h2:mt-10 prose-h2:mb-5 prose-h2:text-blue-800
                    prose-h3:text-xl prose-h3:font-medium prose-h3:mt-8 prose-h3:mb-4 prose-h3:text-blue-700
                    prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-6 prose-p:text-base
                    prose-ul:my-6 prose-ul:list-disc prose-ul:pl-6 prose-ul:space-y-3
                    prose-li:text-gray-700 prose-li:mb-3 prose-li:leading-relaxed
                    prose-strong:text-gray-900 prose-strong:font-semibold
                    prose-em:text-gray-600 prose-em:italic
                    prose-hr:my-8 prose-hr:border-2 prose-hr:border-gray-300
                ">
                    {content ? (
                        <ReactMarkdown>{content}</ReactMarkdown>
                    ) : (
                        <p className="text-gray-400 italic">Waiting for draft...</p>
                    )}
                </div>
            </div>
        </div>
    );
}

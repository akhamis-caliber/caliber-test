import React, { useState } from 'react';

export default function InsightsSidebar({ results = [] }) {
  const [isOpen, setIsOpen] = useState(true);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Mock AI insights based on results
  const generateInsights = () => {
    if (results.length === 0) return 'No data available for analysis.';
    
    const topPerformer = results.reduce((max, result) => 
      result.score > max.score ? result : max
    );
    
    const avgScore = results.reduce((sum, result) => sum + result.score, 0) / results.length;
    const goodPerformers = results.filter(r => r.score >= 80).length;
    const poorPerformers = results.filter(r => r.score < 60).length;
    
    return `Your top-performing domain is ${topPerformer.domain} with a score of ${topPerformer.score}/100, showing ${(topPerformer.conversionRate * 100).toFixed(1)}% conversion rate and $${topPerformer.cpm.toFixed(2)} CPM.

Overall campaign performance:
• Average score: ${avgScore.toFixed(1)}/100
• ${goodPerformers} high-performing publishers (80+ score)
• ${poorPerformers} underperforming publishers (<60 score)

Recommendation: Focus budget allocation on domains scoring above 80, while optimizing or excluding those below 60.`;
  };

  const [insights, setInsights] = useState(generateInsights());

  const regenerateInsights = async () => {
    setIsGenerating(true);
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    setInsights(generateInsights());
    setIsGenerating(false);
  };

  const sendChatMessage = async () => {
    if (!chatMessage.trim()) return;

    const userMessage = { type: 'user', content: chatMessage, timestamp: new Date() };
    setChatHistory(prev => [...prev, userMessage]);
    setChatMessage('');

    // Simulate AI response
    const aiResponse = {
      type: 'ai',
      content: `I understand you're asking about "${chatMessage}". Based on your campaign data, here are some insights that might help...`,
      timestamp: new Date()
    };

    setTimeout(() => {
      setChatHistory(prev => [...prev, aiResponse]);
    }, 1000);
  };

  return (
    <div className={`fixed right-0 top-0 h-full w-80 bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${
      isOpen ? 'translate-x-0' : 'translate-x-full'
    }`}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute -left-12 top-4 bg-indigo-600 text-white p-2 rounded-l-lg hover:bg-indigo-700"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>

      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">AI Insights</h2>
          <p className="text-sm text-gray-500">Powered by GPT</p>
        </div>

        {/* Insights Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Performance Summary */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">Performance Summary</h3>
              <button
                onClick={regenerateInsights}
                disabled={isGenerating}
                className="text-xs text-indigo-600 hover:text-indigo-700 disabled:opacity-50"
              >
                {isGenerating ? 'Generating...' : 'Regenerate'}
              </button>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-700 whitespace-pre-line">
                {insights}
              </p>
            </div>
          </div>

          {/* Chat Assistant */}
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Ask Caliber</h3>
            
            {/* Chat History */}
            <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
              {chatHistory.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                      message.type === 'user'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
            </div>

            {/* Chat Input */}
            <div className="flex space-x-2">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                placeholder="Ask about your campaign..."
                className="flex-1 text-sm border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={sendChatMessage}
                disabled={!chatMessage.trim()}
                className="px-3 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 text-center">
            AI insights are generated based on your campaign data
          </div>
        </div>
      </div>
    </div>
  );
} 
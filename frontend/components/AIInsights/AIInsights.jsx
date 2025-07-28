import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card.jsx';
import { Button } from '../ui/button.jsx';
import { Badge } from '../ui/badge.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs.jsx';
import { Input } from '../ui/input.jsx';
import { Textarea } from '../ui/textarea.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select.jsx';
import { 
    Brain, 
    Lightbulb, 
    MessageSquare, 
    TrendingUp, 
    RefreshCw, 
    Send,
    Sparkles,
    BarChart3,
    Target,
    AlertCircle
} from 'lucide-react';
import { api } from '@/services/api';

const AIInsights = ({ campaignId }) => {
    const [activeTab, setActiveTab] = useState('insights');
    const [loading, setLoading] = useState(false);
    const [insights, setInsights] = useState(null);
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [qaHistory, setQaHistory] = useState([]);
    const [explanation, setExplanation] = useState('');
    const [explanationType, setExplanationType] = useState('comprehensive');
    const [detailLevel, setDetailLevel] = useState('detailed');
    const [selectedReportId, setSelectedReportId] = useState(null);
    const [reports, setReports] = useState([]);
    const [trends, setTrends] = useState(null);
    const [recommendations, setRecommendations] = useState([]);

    useEffect(() => {
        if (campaignId) {
            fetchReports();
        }
    }, [campaignId]);

    const fetchReports = async () => {
        try {
            const response = await api.get(`/api/reports?campaign_id=${campaignId}`);
            setReports(response.data);
        } catch (error) {
            console.error('Error fetching reports:', error);
        }
    };

    const generateInsights = async () => {
        try {
            setLoading(true);
            const response = await api.post('/api/ai/insights', {
                campaign_id: campaignId,
                analysis_type: 'comprehensive',
                include_recommendations: true
            });
            setInsights(response.data);
        } catch (error) {
            console.error('Error generating insights:', error);
        } finally {
            setLoading(false);
        }
    };

    const askQuestion = async () => {
        if (!question.trim()) return;

        try {
            setLoading(true);
            const response = await api.post('/api/ai/qa', null, {
                params: {
                    question: question,
                    campaign_id: campaignId
                }
            });
            
            const newQa = {
                question: question,
                answer: response.data.answer,
                timestamp: new Date().toISOString()
            };
            
            setQaHistory([newQa, ...qaHistory]);
            setAnswer(response.data.answer);
            setQuestion('');
        } catch (error) {
            console.error('Error asking question:', error);
        } finally {
            setLoading(false);
        }
    };

    const generateExplanation = async () => {
        if (!selectedReportId) return;

        try {
            setLoading(true);
            const response = await api.post('/api/ai/explain', {
                report_id: selectedReportId,
                explanation_type: explanationType,
                detail_level: detailLevel
            });
            setExplanation(response.data.explanation);
        } catch (error) {
            console.error('Error generating explanation:', error);
        } finally {
            setLoading(false);
        }
    };

    const generateRecommendations = async () => {
        try {
            setLoading(true);
            const response = await api.post('/api/ai/recommendations', {
                campaign_id: campaignId,
                focus_area: 'performance'
            });
            setRecommendations(response.data.recommendations);
        } catch (error) {
            console.error('Error generating recommendations:', error);
        } finally {
            setLoading(false);
        }
    };

    const analyzeTrends = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/api/ai/trends/${campaignId}?time_period=30d`);
            setTrends(response.data);
        } catch (error) {
            console.error('Error analyzing trends:', error);
        } finally {
            setLoading(false);
        }
    };

    const getInsightIcon = (type) => {
        switch (type) {
            case 'positive': return <TrendingUp className="h-4 w-4 text-green-600" />;
            case 'negative': return <AlertCircle className="h-4 w-4 text-red-600" />;
            case 'neutral': return <BarChart3 className="h-4 w-4 text-blue-600" />;
            default: return <Lightbulb className="h-4 w-4 text-yellow-600" />;
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                    <Brain className="h-8 w-8 text-purple-600" />
                    <h1 className="text-3xl font-bold">AI Insights</h1>
                </div>
                <div className="flex gap-2">
                    <Button onClick={generateInsights} disabled={loading} variant="outline">
                        <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Generate Insights
                    </Button>
                    <Button onClick={analyzeTrends} disabled={loading}>
                        <TrendingUp className="h-4 w-4 mr-2" />
                        Analyze Trends
                    </Button>
                </div>
            </div>

            {/* Main Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-5">
                    <TabsTrigger value="insights">Insights</TabsTrigger>
                    <TabsTrigger value="qa">Q&A</TabsTrigger>
                    <TabsTrigger value="explanations">Explanations</TabsTrigger>
                    <TabsTrigger value="trends">Trends</TabsTrigger>
                    <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
                </TabsList>

                <TabsContent value="insights" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center space-x-2">
                                <Sparkles className="h-5 w-5" />
                                <span>AI-Generated Insights</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {insights ? (
                                <div className="space-y-6">
                                    {/* Key Findings */}
                                    <div>
                                        <h3 className="text-lg font-semibold mb-3">Key Findings</h3>
                                        <div className="grid gap-3">
                                            {insights.key_findings.map((finding, index) => (
                                                <div key={index} className="flex items-start space-x-2 p-3 bg-blue-50 rounded-lg">
                                                    <Target className="h-4 w-4 text-blue-600 mt-0.5" />
                                                    <p className="text-sm">{finding}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Insights */}
                                    <div>
                                        <h3 className="text-lg font-semibold mb-3">Insights</h3>
                                        <div className="grid gap-3">
                                            {insights.insights.map((insight, index) => (
                                                <div key={index} className="flex items-start space-x-2 p-3 bg-green-50 rounded-lg">
                                                    <Lightbulb className="h-4 w-4 text-green-600 mt-0.5" />
                                                    <p className="text-sm">{insight}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Recommendations */}
                                    <div>
                                        <h3 className="text-lg font-semibold mb-3">Recommendations</h3>
                                        <div className="grid gap-3">
                                            {insights.recommendations.map((rec, index) => (
                                                <div key={index} className="flex items-start space-x-2 p-3 bg-purple-50 rounded-lg">
                                                    <TrendingUp className="h-4 w-4 text-purple-600 mt-0.5" />
                                                    <p className="text-sm">{rec}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Data Summary */}
                                    <div>
                                        <h3 className="text-lg font-semibold mb-3">Data Summary</h3>
                                        <div className="grid grid-cols-3 gap-4">
                                            <div className="text-center p-3 bg-gray-50 rounded-lg">
                                                <p className="text-2xl font-bold">{insights.data_summary.total_reports}</p>
                                                <p className="text-sm text-gray-600">Total Reports</p>
                                            </div>
                                            <div className="text-center p-3 bg-gray-50 rounded-lg">
                                                <p className="text-2xl font-bold">{insights.data_summary.average_score.toFixed(1)}</p>
                                                <p className="text-sm text-gray-600">Average Score</p>
                                            </div>
                                            <div className="text-center p-3 bg-gray-50 rounded-lg">
                                                <p className="text-2xl font-bold">{insights.data_summary.score_range.toFixed(1)}</p>
                                                <p className="text-sm text-gray-600">Score Range</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-8">
                                    <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                    <p className="text-gray-600">Click "Generate Insights" to get AI-powered analysis</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="qa" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center space-x-2">
                                <MessageSquare className="h-5 w-5" />
                                <span>Ask Questions About Your Data</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {/* Question Input */}
                                <div className="flex space-x-2">
                                    <Input
                                        placeholder="Ask a question about your scoring data..."
                                        value={question}
                                        onChange={(e) => setQuestion(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
                                    />
                                    <Button onClick={askQuestion} disabled={loading || !question.trim()}>
                                        <Send className="h-4 w-4" />
                                    </Button>
                                </div>

                                {/* Current Answer */}
                                {answer && (
                                    <div className="p-4 bg-blue-50 rounded-lg">
                                        <h4 className="font-semibold mb-2">Answer:</h4>
                                        <p className="text-sm">{answer}</p>
                                    </div>
                                )}

                                {/* Q&A History */}
                                {qaHistory.length > 0 && (
                                    <div>
                                        <h4 className="font-semibold mb-3">Recent Questions</h4>
                                        <div className="space-y-3">
                                            {qaHistory.map((qa, index) => (
                                                <div key={index} className="border rounded-lg p-3">
                                                    <div className="flex items-start space-x-2 mb-2">
                                                        <MessageSquare className="h-4 w-4 text-blue-600 mt-0.5" />
                                                        <p className="font-medium text-sm">{qa.question}</p>
                                                    </div>
                                                    <p className="text-sm text-gray-600 ml-6">{qa.answer}</p>
                                                    <p className="text-xs text-gray-400 ml-6 mt-1">
                                                        {new Date(qa.timestamp).toLocaleString()}
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="explanations" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center space-x-2">
                                <BarChart3 className="h-5 w-5" />
                                <span>Score Explanations</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {/* Report Selection */}
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="text-sm font-medium">Select Report</label>
                                        <Select value={selectedReportId} onValueChange={setSelectedReportId}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Choose a report" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {reports.map((report) => (
                                                    <SelectItem key={report.id} value={report.id.toString()}>
                                                        Report #{report.id}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium">Explanation Type</label>
                                        <Select value={explanationType} onValueChange={setExplanationType}>
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="comprehensive">Comprehensive</SelectItem>
                                                <SelectItem value="summary">Summary</SelectItem>
                                                <SelectItem value="technical">Technical</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium">Detail Level</label>
                                        <Select value={detailLevel} onValueChange={setDetailLevel}>
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="basic">Basic</SelectItem>
                                                <SelectItem value="detailed">Detailed</SelectItem>
                                                <SelectItem value="expert">Expert</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>

                                <Button onClick={generateExplanation} disabled={loading || !selectedReportId}>
                                    Generate Explanation
                                </Button>

                                {explanation && (
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <h4 className="font-semibold mb-2">Explanation:</h4>
                                        <div className="prose prose-sm max-w-none">
                                            {explanation.split('\n').map((paragraph, index) => (
                                                <p key={index} className="mb-2">{paragraph}</p>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="trends" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center space-x-2">
                                <TrendingUp className="h-5 w-5" />
                                <span>Trend Analysis</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {trends ? (
                                <div className="space-y-6">
                                    {/* Trends Summary */}
                                    <div>
                                        <h3 className="text-lg font-semibold mb-3">Trend Summary</h3>
                                        <p className="text-sm text-gray-600">{trends.summary}</p>
                                    </div>

                                    {/* Key Trends */}
                                    <div>
                                        <h3 className="text-lg font-semibold mb-3">Key Trends</h3>
                                        <div className="grid gap-3">
                                            {trends.trends.map((trend, index) => (
                                                <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                                                    <div>
                                                        <p className="font-medium">{trend.metric}</p>
                                                        <p className="text-sm text-gray-600">{trend.description}</p>
                                                    </div>
                                                    <Badge variant={trend.strength === 'strong' ? 'default' : 'secondary'}>
                                                        {trend.trend}
                                                    </Badge>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Insights */}
                                    <div>
                                        <h3 className="text-lg font-semibold mb-3">Insights</h3>
                                        <div className="grid gap-3">
                                            {trends.insights.map((insight, index) => (
                                                <div key={index} className="flex items-start space-x-2 p-3 bg-green-50 rounded-lg">
                                                    <Lightbulb className="h-4 w-4 text-green-600 mt-0.5" />
                                                    <p className="text-sm">{insight}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Forecast */}
                                    {trends.forecast.available && (
                                        <div>
                                            <h3 className="text-lg font-semibold mb-3">Forecast</h3>
                                            <div className="p-3 bg-purple-50 rounded-lg">
                                                <p className="text-sm mb-2">Next 3 periods: {trends.forecast.forecast.map(f => f.toFixed(1)).join(', ')}</p>
                                                <p className="text-xs text-gray-600">Confidence: {trends.forecast.confidence}</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center py-8">
                                    <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                    <p className="text-gray-600">Click "Analyze Trends" to get trend analysis</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center space-x-2">
                                <Target className="h-5 w-5" />
                                <span>AI Recommendations</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <Button onClick={generateRecommendations} disabled={loading}>
                                    Generate Recommendations
                                </Button>

                                {recommendations.length > 0 && (
                                    <div className="space-y-3">
                                        {recommendations.map((rec, index) => (
                                            <div key={index} className="flex items-start space-x-2 p-3 bg-purple-50 rounded-lg">
                                                <Target className="h-4 w-4 text-purple-600 mt-0.5" />
                                                <p className="text-sm">{rec}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default AIInsights; 
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card.jsx';
import { Button } from '../ui/button.jsx';
import { Badge } from '../ui/badge.jsx';
import { Progress } from '../ui/progress.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs.jsx';
import { 
    BarChart, 
    Bar, 
    XAxis, 
    YAxis, 
    CartesianGrid, 
    Tooltip, 
    Legend, 
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    LineChart,
    Line
} from 'recharts';
import { 
    Play, 
    Pause, 
    RefreshCw, 
    TrendingUp, 
    Users, 
    FileText,
    Settings,
    Download
} from 'lucide-react';
import { api } from '@/services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const ScoringDashboard = ({ campaignId }) => {
    const [scoringJobs, setScoringJobs] = useState([]);
    const [scoringSummary, setScoringSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        if (campaignId) {
            fetchScoringData();
        }
    }, [campaignId]);

    const fetchScoringData = async () => {
        try {
            setLoading(true);
            const [jobsResponse, summaryResponse] = await Promise.all([
                api.get(`/api/scoring/jobs?campaign_id=${campaignId}`),
                api.get(`/api/scoring/summary/${campaignId}`)
            ]);
            
            setScoringJobs(jobsResponse.data);
            setScoringSummary(summaryResponse.data);
        } catch (error) {
            console.error('Error fetching scoring data:', error);
        } finally {
            setLoading(false);
        }
    };

    const startScoringJob = async (reportId) => {
        try {
            await api.post('/api/scoring/jobs', {
                report_id: reportId,
                campaign_id: campaignId,
                job_type: 'standard'
            });
            fetchScoringData();
        } catch (error) {
            console.error('Error starting scoring job:', error);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'processing': return 'bg-blue-100 text-blue-800';
            case 'queued': return 'bg-yellow-100 text-yellow-800';
            case 'failed': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const formatScoreDistribution = (distribution) => {
        return Object.entries(distribution).map(([key, value]) => ({
            name: key.charAt(0).toUpperCase() + key.slice(1),
            value,
            color: COLORS[Object.keys(distribution).indexOf(key)]
        }));
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <RefreshCw className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Scoring Dashboard</h1>
                <div className="flex gap-2">
                    <Button onClick={fetchScoringData} variant="outline">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Refresh
                    </Button>
                    <Button>
                        <Download className="h-4 w-4 mr-2" />
                        Export Report
                    </Button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
                        <FileText className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{scoringSummary?.total_records || 0}</div>
                        <p className="text-xs text-muted-foreground">
                            {scoringJobs.filter(job => job.status === 'completed').length} scored
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Average Score</CardTitle>
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {scoringSummary?.average_score?.toFixed(1) || '0.0'}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Target: {scoringSummary?.target_score || 'N/A'}
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
                        <Play className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {scoringJobs.filter(job => job.status === 'processing' || job.status === 'queued').length}
                        </div>
                        <p className="text-xs text-muted-foreground">
                            In progress
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {scoringJobs.length > 0 
                                ? Math.round((scoringJobs.filter(job => job.status === 'completed').length / scoringJobs.length) * 100)
                                : 0}%
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Completed successfully
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="jobs">Scoring Jobs</TabsTrigger>
                    <TabsTrigger value="analytics">Analytics</TabsTrigger>
                    <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Score Distribution Chart */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Score Distribution</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ResponsiveContainer width="100%" height={300}>
                                    <PieChart>
                                        <Pie
                                            data={formatScoreDistribution(scoringSummary?.score_distribution || {})}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                            outerRadius={80}
                                            fill="#8884d8"
                                            dataKey="value"
                                        >
                                            {formatScoreDistribution(scoringSummary?.score_distribution || {}).map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>

                        {/* Score Range Chart */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Score Range</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={[
                                        {
                                            name: 'Min',
                                            score: scoringSummary?.min_score || 0
                                        },
                                        {
                                            name: 'Average',
                                            score: scoringSummary?.average_score || 0
                                        },
                                        {
                                            name: 'Max',
                                            score: scoringSummary?.max_score || 0
                                        }
                                    ]}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip />
                                        <Bar dataKey="score" fill="#8884d8" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="jobs" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Scoring Jobs</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {scoringJobs.map((job) => (
                                    <div key={job.id} className="flex items-center justify-between p-4 border rounded-lg">
                                        <div className="flex items-center space-x-4">
                                            <div>
                                                <p className="font-medium">Job #{job.id}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    Report ID: {job.report_id}
                                                </p>
                                            </div>
                                            <Badge className={getStatusColor(job.status)}>
                                                {job.status}
                                            </Badge>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            {job.status === 'processing' && (
                                                <Progress value={job.progress} className="w-24" />
                                            )}
                                            <span className="text-sm text-muted-foreground">
                                                {new Date(job.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                                {scoringJobs.length === 0 && (
                                    <p className="text-center text-muted-foreground py-8">
                                        No scoring jobs found
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="analytics" className="space-y-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Processing Time Trend */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Processing Time Trend</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart data={scoringJobs
                                        .filter(job => job.status === 'completed')
                                        .slice(-10)
                                        .map(job => ({
                                            name: `Job ${job.id}`,
                                            time: job.processing_time || 0
                                        }))
                                    }>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip />
                                        <Line type="monotone" dataKey="time" stroke="#8884d8" />
                                    </LineChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>

                        {/* Job Status Distribution */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Job Status Distribution</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={Object.entries(
                                        scoringJobs.reduce((acc, job) => {
                                            acc[job.status] = (acc[job.status] || 0) + 1;
                                            return acc;
                                        }, {})
                                    ).map(([status, count]) => ({
                                        status: status.charAt(0).toUpperCase() + status.slice(1),
                                        count
                                    }))}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="status" />
                                        <YAxis />
                                        <Tooltip />
                                        <Bar dataKey="count" fill="#8884d8" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="settings" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Scoring Configuration</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div>
                                    <h3 className="font-medium mb-2">Scoring Templates</h3>
                                    <p className="text-sm text-muted-foreground">
                                        Configure scoring templates and criteria for different campaign types.
                                    </p>
                                </div>
                                <Button>
                                    <Settings className="h-4 w-4 mr-2" />
                                    Configure Templates
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default ScoringDashboard; 
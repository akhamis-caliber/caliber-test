import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card.jsx';
import { Button } from '../ui/button.jsx';
import { Input } from '../ui/input.jsx';
import { Label } from '../ui/label.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select.jsx';
import { Textarea } from '../ui/textarea.jsx';
import { Switch } from '../ui/switch.jsx';
import { Badge } from '../ui/badge.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs.jsx';
import { 
    Plus, 
    Trash2, 
    Save, 
    Copy, 
    Settings,
    AlertCircle,
    CheckCircle
} from 'lucide-react';
import { api } from '@/services/api';

const ScoringConfig = ({ campaignId, onConfigChange }) => {
    const [config, setConfig] = useState({
        metrics: [],
        outlier_config: {
            method: 'iqr',
            action: 'mark'
        },
        normalization_config: {
            method: 'zscore',
            columns: null
        },
        weighting_config: {
            strategy: 'linear',
            metrics: null
        },
        explanation_config: {
            explanation_type: 'score_breakdown',
            include_metrics: null
        }
    });
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(false);
    const [validation, setValidation] = useState({ isValid: true, errors: [] });
    const [activeTab, setActiveTab] = useState('metrics');

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = async () => {
        try {
            const response = await api.get('/api/scoring/templates');
            setTemplates(response.data);
        } catch (error) {
            console.error('Error fetching templates:', error);
        }
    };

    const validateConfig = async () => {
        try {
            setLoading(true);
            const response = await api.post('/api/scoring/config/validate', config);
            setValidation(response.data);
            return response.data.is_valid;
        } catch (error) {
            console.error('Error validating config:', error);
            setValidation({ isValid: false, errors: [{ field: 'general', message: 'Validation failed' }] });
            return false;
        } finally {
            setLoading(false);
        }
    };

    const addMetric = () => {
        const newMetric = {
            metric_name: '',
            metric_type: 'continuous',
            description: '',
            weight: 0.0,
            min_value: null,
            max_value: null,
            normalization_method: 'zscore',
            outlier_method: 'iqr',
            outlier_action: 'mark',
            is_active: true
        };
        setConfig(prev => ({
            ...prev,
            metrics: [...prev.metrics, newMetric]
        }));
    };

    const updateMetric = (index, field, value) => {
        setConfig(prev => ({
            ...prev,
            metrics: prev.metrics.map((metric, i) => 
                i === index ? { ...metric, [field]: value } : metric
            )
        }));
    };

    const removeMetric = (index) => {
        setConfig(prev => ({
            ...prev,
            metrics: prev.metrics.filter((_, i) => i !== index)
        }));
    };

    const applyTemplate = (template) => {
        if (template.config) {
            setConfig(template.config);
        }
    };

    const saveConfig = async () => {
        const isValid = await validateConfig();
        if (isValid && onConfigChange) {
            onConfigChange(config);
        }
    };

    const calculateTotalWeight = () => {
        return config.metrics.reduce((sum, metric) => sum + (metric.weight || 0), 0);
    };

    const getWeightStatus = () => {
        const total = calculateTotalWeight();
        if (Math.abs(total - 1.0) < 0.01) {
            return { valid: true, message: 'Weights balanced' };
        } else if (total < 1.0) {
            return { valid: false, message: `Underweighted by ${(1.0 - total).toFixed(2)}` };
        } else {
            return { valid: false, message: `Overweighted by ${(total - 1.0).toFixed(2)}` };
        }
    };

    const weightStatus = getWeightStatus();

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Scoring Configuration</h2>
                <div className="flex gap-2">
                    <Button onClick={validateConfig} variant="outline" disabled={loading}>
                        {loading ? 'Validating...' : 'Validate'}
                    </Button>
                    <Button onClick={saveConfig}>
                        <Save className="h-4 w-4 mr-2" />
                        Save Configuration
                    </Button>
                </div>
            </div>

            {/* Validation Status */}
            {validation.errors.length > 0 && (
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 text-red-800">
                            <AlertCircle className="h-4 w-4" />
                            <span className="font-medium">Configuration Issues:</span>
                        </div>
                        <ul className="mt-2 space-y-1">
                            {validation.errors.map((error, index) => (
                                <li key={index} className="text-sm text-red-700">
                                    {error.field}: {error.message}
                                </li>
                            ))}
                        </ul>
                    </CardContent>
                </Card>
            )}

            {validation.isValid && config.metrics.length > 0 && (
                <Card className="border-green-200 bg-green-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 text-green-800">
                            <CheckCircle className="h-4 w-4" />
                            <span className="font-medium">Configuration is valid</span>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Templates */}
            <Card>
                <CardHeader>
                    <CardTitle>Scoring Templates</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {templates.map((template) => (
                            <Card key={template.id} className="cursor-pointer hover:shadow-md transition-shadow">
                                <CardContent className="pt-6">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="font-medium">{template.name}</h3>
                                        <Badge variant="secondary">{template.category}</Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground mb-3">
                                        {template.description}
                                    </p>
                                    <Button 
                                        size="sm" 
                                        variant="outline"
                                        onClick={() => applyTemplate(template)}
                                    >
                                        <Copy className="h-4 w-4 mr-2" />
                                        Apply Template
                                    </Button>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Configuration Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="metrics">Metrics</TabsTrigger>
                    <TabsTrigger value="outliers">Outliers</TabsTrigger>
                    <TabsTrigger value="normalization">Normalization</TabsTrigger>
                    <TabsTrigger value="weighting">Weighting</TabsTrigger>
                </TabsList>

                <TabsContent value="metrics" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <div className="flex justify-between items-center">
                                <CardTitle>Scoring Metrics</CardTitle>
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm">Total Weight:</span>
                                        <Badge variant={weightStatus.valid ? "default" : "destructive"}>
                                            {calculateTotalWeight().toFixed(2)}
                                        </Badge>
                                    </div>
                                    <Button onClick={addMetric} size="sm">
                                        <Plus className="h-4 w-4 mr-2" />
                                        Add Metric
                                    </Button>
                                </div>
                            </div>
                            {!weightStatus.valid && (
                                <p className="text-sm text-red-600">{weightStatus.message}</p>
                            )}
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {config.metrics.map((metric, index) => (
                                    <Card key={index} className="p-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                            <div>
                                                <Label>Metric Name</Label>
                                                <Input
                                                    value={metric.metric_name}
                                                    onChange={(e) => updateMetric(index, 'metric_name', e.target.value)}
                                                    placeholder="e.g., Revenue"
                                                />
                                            </div>
                                            <div>
                                                <Label>Type</Label>
                                                <Select 
                                                    value={metric.metric_type} 
                                                    onValueChange={(value) => updateMetric(index, 'metric_type', value)}
                                                >
                                                    <SelectTrigger>
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="continuous">Continuous</SelectItem>
                                                        <SelectItem value="categorical">Categorical</SelectItem>
                                                        <SelectItem value="binary">Binary</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div>
                                                <Label>Weight</Label>
                                                <Input
                                                    type="number"
                                                    step="0.01"
                                                    min="0"
                                                    max="1"
                                                    value={metric.weight}
                                                    onChange={(e) => updateMetric(index, 'weight', parseFloat(e.target.value) || 0)}
                                                />
                                            </div>
                                            <div className="flex items-end">
                                                <Button 
                                                    variant="outline" 
                                                    size="sm"
                                                    onClick={() => removeMetric(index)}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <Label>Description</Label>
                                                <Textarea
                                                    value={metric.description}
                                                    onChange={(e) => updateMetric(index, 'description', e.target.value)}
                                                    placeholder="Describe this metric..."
                                                />
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <Label>Min Value</Label>
                                                    <Input
                                                        type="number"
                                                        value={metric.min_value || ''}
                                                        onChange={(e) => updateMetric(index, 'min_value', parseFloat(e.target.value) || null)}
                                                        placeholder="Optional"
                                                    />
                                                </div>
                                                <div>
                                                    <Label>Max Value</Label>
                                                    <Input
                                                        type="number"
                                                        value={metric.max_value || ''}
                                                        onChange={(e) => updateMetric(index, 'max_value', parseFloat(e.target.value) || null)}
                                                        placeholder="Optional"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                                {config.metrics.length === 0 && (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <Settings className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                        <p>No metrics configured. Add your first metric to get started.</p>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="outliers" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Outlier Detection</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <Label>Detection Method</Label>
                                    <Select 
                                        value={config.outlier_config.method} 
                                        onValueChange={(value) => setConfig(prev => ({
                                            ...prev,
                                            outlier_config: { ...prev.outlier_config, method: value }
                                        }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="iqr">IQR Method</SelectItem>
                                            <SelectItem value="zscore">Z-Score</SelectItem>
                                            <SelectItem value="isolation_forest">Isolation Forest</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div>
                                    <Label>Action</Label>
                                    <Select 
                                        value={config.outlier_config.action} 
                                        onValueChange={(value) => setConfig(prev => ({
                                            ...prev,
                                            outlier_config: { ...prev.outlier_config, action: value }
                                        }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="mark">Mark as Outlier</SelectItem>
                                            <SelectItem value="remove">Remove</SelectItem>
                                            <SelectItem value="cap">Cap Values</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="normalization" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Data Normalization</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <Label>Normalization Method</Label>
                                    <Select 
                                        value={config.normalization_config.method} 
                                        onValueChange={(value) => setConfig(prev => ({
                                            ...prev,
                                            normalization_config: { ...prev.normalization_config, method: value }
                                        }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="zscore">Z-Score</SelectItem>
                                            <SelectItem value="minmax">Min-Max Scaling</SelectItem>
                                            <SelectItem value="robust">Robust Scaling</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <Switch 
                                        id="auto-normalize"
                                        checked={config.normalization_config.columns === null}
                                        onCheckedChange={(checked) => setConfig(prev => ({
                                            ...prev,
                                            normalization_config: { 
                                                ...prev.normalization_config, 
                                                columns: checked ? null : [] 
                                            }
                                        }))}
                                    />
                                    <Label htmlFor="auto-normalize">Auto-detect columns</Label>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="weighting" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Weighting Strategy</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <Label>Weighting Strategy</Label>
                                    <Select 
                                        value={config.weighting_config.strategy} 
                                        onValueChange={(value) => setConfig(prev => ({
                                            ...prev,
                                            weighting_config: { ...prev.weighting_config, strategy: value }
                                        }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="linear">Linear</SelectItem>
                                            <SelectItem value="exponential">Exponential</SelectItem>
                                            <SelectItem value="logarithmic">Logarithmic</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <Switch 
                                        id="auto-metrics"
                                        checked={config.weighting_config.metrics === null}
                                        onCheckedChange={(checked) => setConfig(prev => ({
                                            ...prev,
                                            weighting_config: { 
                                                ...prev.weighting_config, 
                                                metrics: checked ? null : [] 
                                            }
                                        }))}
                                    />
                                    <Label htmlFor="auto-metrics">Use all metrics</Label>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default ScoringConfig; 
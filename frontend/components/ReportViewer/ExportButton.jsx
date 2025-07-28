import React, { useState } from 'react';
import { Button } from '../ui/button.jsx';
import { Badge } from '../ui/badge.jsx';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
} from '../ui/dropdown-menu.jsx';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog.jsx';
import { Input } from '../ui/input.jsx';
import { Label } from '../ui/label.jsx';
import { Checkbox } from '../ui/checkbox.jsx';
import { Textarea } from '../ui/textarea.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select.jsx';
import {
  Download,
  FileText,
  FileSpreadsheet,
  File,
  Settings,
  Check,
  Loader2,
  AlertCircle
} from 'lucide-react';

const ExportButton = ({ 
  data, 
  reportName = "Report",
  onExport,
  showAdvanced = true,
  className = ""
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState('pdf');
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeInsights, setIncludeInsights] = useState(true);
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [customFileName, setCustomFileName] = useState('');
  const [customNotes, setCustomNotes] = useState('');
  const [exportQuality, setExportQuality] = useState('high');
  const [showDialog, setShowDialog] = useState(false);

  const exportOptions = [
    {
      id: 'pdf',
      label: 'PDF Report',
      icon: File,
      description: 'Professional PDF with charts and insights',
      color: 'text-red-600'
    },
    {
      id: 'excel',
      label: 'Excel Spreadsheet',
      icon: FileSpreadsheet,
      description: 'Data in Excel format with formatting',
      color: 'text-green-600'
    },
    {
      id: 'csv',
      label: 'CSV Data',
      icon: FileText,
      description: 'Raw data in CSV format',
      color: 'text-blue-600'
    }
  ];

  const qualityOptions = [
    { value: 'low', label: 'Low (Fast)', description: 'Basic quality, faster export' },
    { value: 'medium', label: 'Medium', description: 'Balanced quality and speed' },
    { value: 'high', label: 'High (Slow)', description: 'Best quality, slower export' }
  ];

  const getDefaultFileName = () => {
    const timestamp = new Date().toISOString().split('T')[0];
    return `${reportName}_${timestamp}`;
  };

  const handleQuickExport = async (format) => {
    setIsExporting(true);
    try {
      const exportConfig = {
        format,
        fileName: getDefaultFileName(),
        includeCharts: true,
        includeInsights: true,
        includeMetadata: true,
        quality: 'medium',
        notes: ''
      };

      if (onExport) {
        await onExport(exportConfig);
      } else {
        // Default export behavior
        await performExport(exportConfig);
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleAdvancedExport = async () => {
    setIsExporting(true);
    try {
      const exportConfig = {
        format: exportFormat,
        fileName: customFileName || getDefaultFileName(),
        includeCharts,
        includeInsights,
        includeMetadata,
        quality: exportQuality,
        notes: customNotes
      };

      if (onExport) {
        await onExport(exportConfig);
      } else {
        await performExport(exportConfig);
      }
      
      setShowDialog(false);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const performExport = async (config) => {
    // Simulate export process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const { format, fileName } = config;
    
    switch (format) {
      case 'pdf':
        // This would integrate with a PDF generation library
        console.log('Generating PDF:', config);
        break;
      case 'excel':
        // This would integrate with an Excel generation library
        console.log('Generating Excel:', config);
        break;
      case 'csv':
        // Generate CSV
        const csvContent = generateCSV(data);
        downloadFile(csvContent, `${fileName}.csv`, 'text/csv');
        break;
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  };

  const generateCSV = (data) => {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [
      headers.join(','),
      ...data.map(row => headers.map(header => row[header]).join(','))
    ];
    
    return csvRows.join('\n');
  };

  const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const selectedFormat = exportOptions.find(option => option.id === exportFormat);
  const IconComponent = selectedFormat?.icon || Download;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button 
            variant="outline" 
            className={className}
            disabled={isExporting}
          >
            {isExporting ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-2" />
            )}
            {isExporting ? 'Exporting...' : 'Export'}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56">
          <DropdownMenuLabel>Quick Export</DropdownMenuLabel>
          {exportOptions.map((option) => {
            const OptionIcon = option.icon;
            return (
              <DropdownMenuItem
                key={option.id}
                onClick={() => handleQuickExport(option.id)}
                disabled={isExporting}
                className="flex items-center gap-2"
              >
                <OptionIcon className={`w-4 h-4 ${option.color}`} />
                <div className="flex-1">
                  <div className="font-medium">{option.label}</div>
                  <div className="text-xs text-gray-500">{option.description}</div>
                </div>
              </DropdownMenuItem>
            );
          })}
          
          {showAdvanced && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Advanced Options</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => setShowDialog(true)}>
                <Settings className="w-4 h-4 mr-2" />
                Customize Export
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Customize Export</DialogTitle>
            <DialogDescription>
              Configure export options and settings for your report.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Format Selection */}
            <div className="space-y-2">
              <Label>Export Format</Label>
              <Select value={exportFormat} onValueChange={setExportFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {exportOptions.map((option) => {
                    const OptionIcon = option.icon;
                    return (
                      <SelectItem key={option.id} value={option.id}>
                        <div className="flex items-center gap-2">
                          <OptionIcon className={`w-4 h-4 ${option.color}`} />
                          {option.label}
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {/* File Name */}
            <div className="space-y-2">
              <Label>File Name</Label>
              <Input
                value={customFileName}
                onChange={(e) => setCustomFileName(e.target.value)}
                placeholder={getDefaultFileName()}
              />
            </div>

            {/* Export Options */}
            <div className="space-y-3">
              <Label>Export Options</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeCharts"
                    checked={includeCharts}
                    onCheckedChange={setIncludeCharts}
                  />
                  <Label htmlFor="includeCharts">Include Charts & Visualizations</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeInsights"
                    checked={includeInsights}
                    onCheckedChange={setIncludeInsights}
                  />
                  <Label htmlFor="includeInsights">Include AI Insights</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeMetadata"
                    checked={includeMetadata}
                    onCheckedChange={setIncludeMetadata}
                  />
                  <Label htmlFor="includeMetadata">Include Metadata</Label>
                </div>
              </div>
            </div>

            {/* Quality Setting */}
            {exportFormat === 'pdf' && (
              <div className="space-y-2">
                <Label>Export Quality</Label>
                <Select value={exportQuality} onValueChange={setExportQuality}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {qualityOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        <div>
                          <div className="font-medium">{option.label}</div>
                          <div className="text-xs text-gray-500">{option.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Custom Notes */}
            <div className="space-y-2">
              <Label>Custom Notes (Optional)</Label>
              <Textarea
                value={customNotes}
                onChange={(e) => setCustomNotes(e.target.value)}
                placeholder="Add any additional notes or comments..."
                rows={3}
              />
            </div>

            {/* Export Summary */}
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="text-sm font-medium mb-2">Export Summary</div>
              <div className="space-y-1 text-sm text-gray-600">
                <div>Format: <Badge variant="outline">{selectedFormat?.label}</Badge></div>
                <div>File: {customFileName || getDefaultFileName()}.{exportFormat}</div>
                <div>Options: {[
                  includeCharts && 'Charts',
                  includeInsights && 'Insights',
                  includeMetadata && 'Metadata'
                ].filter(Boolean).join(', ')}</div>
                {exportFormat === 'pdf' && (
                  <div>Quality: <Badge variant="outline">{exportQuality}</Badge></div>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDialog(false)}
              disabled={isExporting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAdvancedExport}
              disabled={isExporting}
            >
              {isExporting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Export Report
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ExportButton; 
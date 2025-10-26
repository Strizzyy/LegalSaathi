import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Bell, 
  CheckCircle, 
  AlertTriangle, 
  Info,
  Camera,
  FileText,
  Zap,
  BarChart3
} from 'lucide-react';
import { processingNotificationService } from '../services/processingNotificationService';

export const DynamicNotificationDemo = React.memo(function DynamicNotificationDemo() {
  const [selectedDemo, setSelectedDemo] = useState<string | null>(null);

  const demoScenarios = [
    {
      id: 'high-confidence',
      title: 'High Confidence OCR',
      description: 'Clear image with excellent text recognition',
      icon: <CheckCircle className="w-6 h-6 text-green-400" />,
      color: 'border-green-500/30 bg-green-500/10',
      action: () => {
        processingNotificationService.showProcessingNotifications({
          success: true,
          confidence_scores: {
            average_confidence: 0.92,
            high_confidence_ratio: 0.88,
            total_text_blocks: 25,
            high_confidence_blocks: 22
          },
          processing_metadata: {
            api_used: 'Google Cloud Vision API'
          }
        }, 'contract-scan.jpg');
      }
    },
    {
      id: 'low-confidence',
      title: 'Low Confidence OCR',
      description: 'Blurry image with poor text recognition',
      icon: <AlertTriangle className="w-6 h-6 text-yellow-400" />,
      color: 'border-yellow-500/30 bg-yellow-500/10',
      action: () => {
        processingNotificationService.showProcessingNotifications({
          success: true,
          confidence_scores: {
            average_confidence: 0.35,
            high_confidence_ratio: 0.12,
            total_text_blocks: 30,
            high_confidence_blocks: 4
          },
          processing_metadata: {
            api_used: 'Google Cloud Vision API'
          }
        }, 'blurry-document.jpg');
      }
    },
    {
      id: 'fallback-processing',
      title: 'Fallback Processing',
      description: 'Vision API unavailable, using fallback',
      icon: <Info className="w-6 h-6 text-blue-400" />,
      color: 'border-blue-500/30 bg-blue-500/10',
      action: () => {
        processingNotificationService.showProcessingNotifications({
          success: true,
          fallback_used: true,
          processing_metadata: {
            api_used: 'Fallback Processing',
            fallback_used: true
          }
        }, 'document.pdf');
      }
    },
    {
      id: 'mixed-quality',
      title: 'Mixed Quality Batch',
      description: 'Batch with varying OCR quality',
      icon: <BarChart3 className="w-6 h-6 text-purple-400" />,
      color: 'border-purple-500/30 bg-purple-500/10',
      action: () => {
        const mockBatchResult = {
          results: [
            {
              file: new File([''], 'good-scan.jpg', { type: 'image/jpeg' }),
              result: {
                success: true,
                confidence_scores: { average_confidence: 0.89 }
              },
              processingTime: 2100
            },
            {
              file: new File([''], 'poor-scan.jpg', { type: 'image/jpeg' }),
              result: {
                success: true,
                confidence_scores: { average_confidence: 0.42 }
              },
              processingTime: 2800
            },
            {
              file: new File([''], 'contract.pdf', { type: 'application/pdf' }),
              result: {
                success: true,
                processing_metadata: { api_used: 'Document AI' }
              },
              processingTime: 1900
            }
          ],
          totalTime: 6800
        };
        
        processingNotificationService.showBatchNotifications(mockBatchResult);
      }
    },
    {
      id: 'file-types',
      title: 'Mixed File Types',
      description: 'Documents and images together',
      icon: <FileText className="w-6 h-6 text-cyan-400" />,
      color: 'border-cyan-500/30 bg-cyan-500/10',
      action: () => {
        const mockFiles = [
          new File([''], 'contract.pdf', { type: 'application/pdf' }),
          new File([''], 'scan1.jpg', { type: 'image/jpeg' }),
          new File([''], 'scan2.png', { type: 'image/png' }),
          new File([''], 'agreement.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
        ];
        
        processingNotificationService.showFileTypeNotifications(mockFiles);
      }
    },
    {
      id: 'performance',
      title: 'Performance Feedback',
      description: 'Fast batch processing notification',
      icon: <Zap className="w-6 h-6 text-green-400" />,
      color: 'border-green-500/30 bg-green-500/10',
      action: () => {
        processingNotificationService.showPerformanceNotifications(4200, 5);
      }
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            🔔 Dynamic Notification System
          </h1>
          <p className="text-xl text-slate-300">
            Contextual notifications based on processing results
          </p>
        </motion.div>

        {/* Info Box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-2xl p-6 mb-8"
        >
          <div className="flex items-start space-x-4">
            <Bell className="w-8 h-8 text-blue-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-xl font-bold text-blue-400 mb-2">
                Smart Notifications
              </h3>
              <p className="text-slate-300 mb-2">
                Instead of static processing notes, the system now shows dynamic notifications based on actual results:
              </p>
              <ul className="text-slate-300 text-sm space-y-1">
                <li>• <strong>OCR Confidence:</strong> Warns about low-quality text extraction</li>
                <li>• <strong>Processing Method:</strong> Shows which API was used</li>
                <li>• <strong>Batch Results:</strong> Summarizes success/failure rates</li>
                <li>• <strong>Performance:</strong> Provides timing feedback</li>
                <li>• <strong>Tips & Actions:</strong> Actionable suggestions for improvement</li>
              </ul>
            </div>
          </div>
        </motion.div>

        {/* Demo Scenarios */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-6"
        >
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
            <Camera className="w-6 h-6 mr-2" />
            Try Different Scenarios
          </h2>

          <div className="grid md:grid-cols-2 gap-4">
            {demoScenarios.map((scenario, index) => (
              <motion.button
                key={scenario.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * index }}
                onClick={() => {
                  setSelectedDemo(scenario.id);
                  scenario.action();
                }}
                className={`p-6 rounded-xl border transition-all duration-300 text-left hover:scale-105 focus:outline-none focus:ring-2 focus:ring-cyan-500 ${
                  selectedDemo === scenario.id 
                    ? scenario.color + ' scale-105' 
                    : 'border-slate-600 bg-slate-800/30 hover:border-slate-500'
                }`}
              >
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    {scenario.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {scenario.title}
                    </h3>
                    <p className="text-slate-400 text-sm">
                      {scenario.description}
                    </p>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-12 bg-slate-800/50 border border-slate-600 rounded-2xl p-6"
        >
          <h3 className="text-lg font-bold text-white mb-4">
            How It Works
          </h3>
          <div className="grid md:grid-cols-2 gap-6 text-slate-300 text-sm">
            <div>
              <h4 className="font-semibold text-white mb-2">🎯 Context-Aware</h4>
              <ul className="space-y-1">
                <li>• Analyzes actual processing results</li>
                <li>• Shows relevant warnings and tips</li>
                <li>• Adapts to different file types</li>
                <li>• Provides actionable feedback</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-2">⏱️ Temporary Display</h4>
              <ul className="space-y-1">
                <li>• Notifications auto-dismiss after 3-8 seconds</li>
                <li>• No permanent UI clutter</li>
                <li>• Important warnings stay longer</li>
                <li>• Action buttons for helpful tips</li>
              </ul>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-slate-700/50 rounded-lg">
            <p className="text-slate-300 text-sm">
              <strong>💡 Try it:</strong> Click the scenarios above to see different types of notifications. 
              Each one shows contextual information based on simulated processing results.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
});

export default DynamicNotificationDemo;
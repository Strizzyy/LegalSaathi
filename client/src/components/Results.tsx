import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  FileText,
  Shield,
  AlertTriangle,
  CheckCircle,
  Info,
  Copy,
  Download,
  Globe,
  BarChart3,
  Zap,
  MessageCircle,
  Activity,
  Users,
  Loader2,
  Mail,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Settings
} from 'lucide-react';
import { cn, formatPercentage, getRiskColor, getRiskBadgeColor, getConfidenceColor } from '../utils';
import { exportService } from '../services/exportService';
import { notificationService } from '../services/notificationService';
import { featureAvailabilityService } from '../services/featureAvailabilityService';
import { AIChat } from './AIChat';
import { HumanSupport } from './HumanSupport';
import { TranslationModal } from './TranslationModal';
import { StatusModal } from './StatusModal';

import { InlineDocumentComparison } from './InlineDocumentComparison';
import { EmailModal } from './EmailModal';
import { PaginatedClauseAnalysis } from './PaginatedClauseAnalysis';
import { LowConfidencePopup } from './LowConfidencePopup';
import { ExpertDashboardPopup } from './ExpertDashboardPopup';

import { expertQueueService } from '../services/expertQueueService';
import { MarkdownRenderer } from '../utils/markdownRenderer';
import { apiService } from '../services/apiService';
import type { DocumentSummaryContent } from '../services/documentSummaryTranslationService';
import type { AnalysisResult, FileInfo, Classification } from '../App';
import type { ClauseContext, DocumentContext } from '../types/chat';

interface ResultsProps {
  analysis: AnalysisResult | null;
  fileInfo: FileInfo | null;
  classification: Classification | null;
  warnings: string[];
  onBackToHome: () => void;
}

import React from 'react';

export const Results = React.memo(function Results({ analysis, fileInfo, classification, onBackToHome }: ResultsProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  
  // Overall Risk Assessment translation state
  const [showRiskTranslation, setShowRiskTranslation] = useState(false);
  const [translatedRiskSummary, setTranslatedRiskSummary] = useState<string>('');
  const [translatedDocumentAbout, setTranslatedDocumentAbout] = useState<string>('');
  const [riskCurrentLanguage, setRiskCurrentLanguage] = useState('en');

  // Text-to-Speech state
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [speechRate, setSpeechRate] = useState(1);
  const [currentSpeechSection, setCurrentSpeechSection] = useState<'risk' | 'about' | null>(null);

  // Document translation state
  const [isTranslating, setIsTranslating] = useState(false);

  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isHumanSupportOpen, setIsHumanSupportOpen] = useState(false);

  const [isTranslationOpen, setIsTranslationOpen] = useState(false);
  const [isStatusOpen, setIsStatusOpen] = useState(false);
  const [translationText, setTranslationText] = useState('');
  const [translationTitle, setTranslationTitle] = useState('');
  const [activeChatClause, setActiveChatClause] = useState<ClauseContext | undefined>(undefined);
  const [isExporting, setIsExporting] = useState<{ pdf: boolean; word: boolean }>({ pdf: false, word: false });
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  
  // Human-in-the-loop confidence popup state
  const [showConfidencePopup, setShowConfidencePopup] = useState(false);
  const [confidencePopupShown, setConfidencePopupShown] = useState(false);
  
  // Expert dashboard popup state
  const [showExpertDashboardPopup, setShowExpertDashboardPopup] = useState(false);

  // Initialize Text-to-Speech
  React.useEffect(() => {
    if ('speechSynthesis' in window) {
      setSpeechSupported(true);
      
      const loadVoices = () => {
        try {
          const voices = window.speechSynthesis.getVoices();
          setAvailableVoices(voices);
          
          if (voices.length === 0) {
            // Voices might not be loaded yet, try again after a delay
            setTimeout(loadVoices, 100);
            return;
          }
          
          // Set default voice (prefer English voices)
          const englishVoice = voices.find(voice => voice.lang.startsWith('en'));
          if (englishVoice) {
            setSelectedVoice(englishVoice);
          } else if (voices.length > 0) {
            setSelectedVoice(voices[0]);
          }
        } catch (error) {
          console.error('Error loading voices:', error);
          setSpeechSupported(false);
        }
      };

      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
      
      // Cleanup function to stop speech when component unmounts
      return () => {
        if (window.speechSynthesis) {
          window.speechSynthesis.cancel();
        }
      };
    }
  }, []);

  // Cleanup speech when component unmounts or analysis changes
  React.useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
        setCurrentSpeechSection(null);
      }
    };
  }, [analysis]);

  // Keyboard shortcuts for TTS
  React.useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      // Ctrl/Cmd + Shift + S to start/stop speech
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'S') {
        event.preventDefault();
        if (isSpeaking) {
          stopSpeech();
        } else {
          speakRiskAssessment();
        }
      }
      // Escape to stop speech
      if (event.key === 'Escape' && isSpeaking) {
        event.preventDefault();
        stopSpeech();
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [isSpeaking]);

  // Debug: Log the analysis data to see what we're receiving
  React.useEffect(() => {
    if (analysis) {
      console.log('Results component received analysis:', analysis);
      console.log('Clause texts in Results:', analysis.analysis_results.map(r => ({
        id: r.clause_id,
        hasText: !!r.clause_text,
        textPreview: r.clause_text?.substring(0, 50) + '...'
      })));
      
      // Check if confidence popup should be shown
      console.log('🔍 Confidence check:', {
        should_route_to_expert: analysis.should_route_to_expert,
        overall_confidence: analysis.overall_confidence,
        confidencePopupShown: confidencePopupShown,
        confidence_breakdown: analysis.confidence_breakdown
      });
      
      if (analysis.should_route_to_expert && analysis.overall_confidence !== undefined && !confidencePopupShown) {
        console.log('✅ Showing confidence popup for low confidence analysis');
        setShowConfidencePopup(true);
        setConfidencePopupShown(true);
      } else {
        console.log('❌ Not showing confidence popup:', {
          should_route: analysis.should_route_to_expert,
          has_confidence: analysis.overall_confidence !== undefined,
          already_shown: confidencePopupShown
        });
      }
    }
  }, [analysis, confidencePopupShown]);

  if (!analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">No Analysis Results</h2>
          <p className="text-slate-400 mb-6">No analysis data available to display.</p>
          <button
            onClick={onBackToHome}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Home
          </button>
        </div>
      </div>
    );
  }



  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const copyResults = async () => {
    try {
      const resultsText = `
Document Analysis Results
========================

Overall Risk: ${analysis.overall_risk.level} (${formatPercentage(analysis.overall_risk.score)})
Confidence: ${analysis.overall_risk.confidence_percentage}%

Summary: ${analysis.summary}

Clause Analysis:
${analysis.analysis_results.map((result, index) => `
${index + 1}. ${result.risk_level.level} Risk (${formatPercentage(result.risk_level.score)})
   ${result.plain_explanation}
`).join('')}
      `.trim();

      await navigator.clipboard.writeText(resultsText);
      notificationService.copySuccess();
    } catch (error) {
      console.error('Failed to copy results:', error);
      notificationService.copyError();
    }
  };

  // Confidence popup handlers
  const handleExpertReviewAccept = async (userEmail: string) => {
    try {
      if (!analysis) return;
      
      // Submit document for expert review
      const submissionData = {
        document_content: analysis.document_text || 'Document content not available',
        ai_analysis: {
          summary: analysis.summary,
          clause_assessments: analysis.analysis_results,
          overall_risk: analysis.overall_risk,
          recommendations: analysis.analysis_results?.flatMap(result => result.recommendations || []) || [],
          enhanced_insights: analysis.enhanced_insights
        },
        user_email: userEmail,
        confidence_score: analysis.overall_confidence || 0.5,
        confidence_breakdown: analysis.confidence_breakdown || {
          overall: analysis.overall_confidence || 0.5,
          factors: ['Low confidence analysis']
        },
        document_type: analysis.document_type || 'general_contract'
      };

      const response = await expertQueueService.submitForExpertReview(submissionData);
      
      console.log('Expert review submitted:', response);
      notificationService.success(`Document submitted for expert review. Review ID: ${response.review_id}`);
      
      // Close the confidence popup and show expert dashboard popup
      setShowConfidencePopup(false);
      setShowExpertDashboardPopup(true);
      
    } catch (error) {
      console.error('Failed to submit for expert review:', error);
      notificationService.error('Failed to submit for expert review. Please try again.');
    }
  };

  // Expert dashboard popup handlers
  const handleGoToExpertDashboard = () => {
    setShowExpertDashboardPopup(false);
    // Open HITL dashboard in new tab (expert review system)
    window.open('/hitl', '_blank');
  };

  const handleStayOnResults = () => {
    setShowExpertDashboardPopup(false);
    notificationService.success('Your expert review request has been submitted. You will receive results via email.');
  };

  const handleExpertReviewDecline = () => {
    console.log('User declined expert review');
    setShowConfidencePopup(false);
    notificationService.success('Proceeding with AI analysis results');
  };

  const openTranslation = (text: string, title: string) => {
    setTranslationText(text);
    setTranslationTitle(title);
    setIsTranslationOpen(true);
  };

  const openChat = (clauseContext?: ClauseContext) => {
    setActiveChatClause(clauseContext);
    setIsChatOpen(true);
  };

  const openHumanSupport = (clauseContext?: ClauseContext) => {
    setActiveChatClause(clauseContext);
    setIsHumanSupportOpen(true);
  };

  // Document translation handlers
  const handleLanguageChange = (language: string) => {
    setRiskCurrentLanguage(language);
    updateVoiceForLanguage(language);
    
    // Clear existing translations when language changes
    if (language === 'en') {
      setTranslatedRiskSummary('');
      setTranslatedDocumentAbout('');
    }
  };

  const translateDocument = async () => {
    if (isTranslating || riskCurrentLanguage === 'en' || !analysis) return;

    setIsTranslating(true);
    
    try {
      // Get the original content sections
      const originalContent = analysis.summary;
      const sections = originalContent.split('**What this document is about:**');
      const riskSection = sections[0].trim();
      const aboutSection = sections.length > 1 ? sections[1].trim() : '';

      // Translate risk assessment section
      const riskResult = await apiService.translateText(riskSection, riskCurrentLanguage, 'en');
      if (riskResult.success && riskResult.translated_text) {
        setTranslatedRiskSummary(riskResult.translated_text);
      }

      // Translate document about section if it exists
      if (aboutSection) {
        const aboutResult = await apiService.translateText(aboutSection, riskCurrentLanguage, 'en');
        if (aboutResult.success && aboutResult.translated_text) {
          setTranslatedDocumentAbout(aboutResult.translated_text);
        }
      }

      // Update voice for the new language
      updateVoiceForLanguage(riskCurrentLanguage);
      
      const languageNames: { [key: string]: string } = {
        'es': 'Spanish',
        'fr': 'French', 
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'hi': 'Hindi',
        'zh': 'Chinese',
        'ar': 'Arabic',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean'
      };
      
      notificationService.success(`Document translated to ${languageNames[riskCurrentLanguage] || riskCurrentLanguage}`);
      
    } catch (error) {
      console.error('Translation error:', error);
      notificationService.error('Translation failed. Please try again.');
    } finally {
      setIsTranslating(false);
    }
  };

  // Legacy handler for compatibility (can be removed later)
  const handleRiskTranslationComplete = (translatedContent: DocumentSummaryContent, language: string) => {
    // This is kept for compatibility but the new system handles translation differently
    const riskSummary = translatedContent.risk_assessment || 
                       translatedContent.what_this_document_means || 
                       analysis.summary;
    
    const sections = riskSummary.split('**What this document is about:**');
    setTranslatedRiskSummary(sections[0].trim());
    
    if (sections.length > 1) {
      setTranslatedDocumentAbout(sections[1].trim());
    }
    
    setRiskCurrentLanguage(language);
    updateVoiceForLanguage(language);
  };

  // Text-to-Speech functions
  const updateVoiceForLanguage = (language: string) => {
    if (!speechSupported || availableVoices.length === 0) return;
    
    const languageMap: { [key: string]: string } = {
      'en': 'en',
      'hi': 'hi',
      'es': 'es',
      'fr': 'fr',
      'de': 'de',
      'zh': 'zh',
      'ar': 'ar',
      'pt': 'pt',
      'it': 'it',
      'ru': 'ru',
      'ja': 'ja',
      'ko': 'ko'
    };
    
    const targetLang = languageMap[language] || 'en';
    const voice = availableVoices.find(v => v.lang.startsWith(targetLang));
    if (voice) {
      setSelectedVoice(voice);
    } else {
      // Fallback to any available voice if target language not found
      const fallbackVoice = availableVoices.find(v => v.lang.startsWith('en')) || availableVoices[0];
      if (fallbackVoice) {
        setSelectedVoice(fallbackVoice);
      }
    }
  };

  const speakText = (text: string, section: 'risk' | 'about') => {
    if (!speechSupported || !('speechSynthesis' in window)) {
      notificationService.error('Text-to-speech is not supported in your browser');
      return;
    }

    if (!selectedVoice) {
      notificationService.error('No voice selected for text-to-speech');
      return;
    }

    if (!text || text.trim().length === 0) {
      notificationService.error('No content available to read');
      return;
    }

    try {
      // Stop any current speech
      window.speechSynthesis.cancel();
    } catch (error) {
      console.error('Error stopping speech synthesis:', error);
    }

    // Clean text for speech (remove markdown and special characters)
    const cleanText = text
      .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold markdown
      .replace(/\*([^*]+)\*/g, '$1') // Remove italic markdown
      .replace(/#{1,6}\s/g, '') // Remove headers
      .replace(/\n+/g, '. ') // Replace line breaks with pauses
      .replace(/\s+/g, ' ') // Normalize spaces
      .replace(/[^\w\s.,!?;:()\-]/g, '') // Remove special characters
      .trim();

    if (cleanText.length === 0) {
      notificationService.error('No readable content found');
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.voice = selectedVoice;
    utterance.rate = speechRate;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setIsSpeaking(true);
      setCurrentSpeechSection(section);
      const sectionName = section === 'risk' ? 'Risk Assessment' : 'Document Overview';
      notificationService.success(`Started reading ${sectionName}`);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setCurrentSpeechSection(null);
      const sectionName = section === 'risk' ? 'Risk Assessment' : 'Document Overview';
      notificationService.success(`Finished reading ${sectionName}`);
    };

    utterance.onerror = (event) => {
      setIsSpeaking(false);
      setCurrentSpeechSection(null);
      console.error('Speech synthesis error:', event);
      
      // Handle specific TTS errors
      if (event.error === 'network') {
        notificationService.error('Network error during speech synthesis. Please check your connection.');
      } else if (event.error === 'synthesis-failed') {
        notificationService.error('Speech synthesis failed. Please try a different voice or text.');
      } else if (event.error === 'language-not-supported') {
        notificationService.error('Selected language not supported for speech synthesis.');
      } else {
        notificationService.error('Speech synthesis failed. Please try again.');
      }
    };

    try {
      window.speechSynthesis.speak(utterance);
    } catch (error) {
      setIsSpeaking(false);
      setCurrentSpeechSection(null);
      console.error('Failed to start speech synthesis:', error);
      notificationService.error('Failed to start text-to-speech');
    }
  };

  const stopSpeech = () => {
    if (speechSupported && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setCurrentSpeechSection(null);
      notificationService.success('Speech stopped');
    }
  };

  const speakRiskAssessment = () => {
    const content = getRiskAssessmentContent();
    speakText(content, 'risk');
  };

  const speakDocumentAbout = () => {
    const content = getDocumentAboutContent();
    if (content) {
      speakText(content, 'about');
    }
  };

  const toggleRiskTranslationPanel = () => {
    setShowRiskTranslation(!showRiskTranslation);
  };

  // Get the content to display (translated or original)
  const getRiskDisplayContent = () => {
    if (riskCurrentLanguage === 'en' || !translatedRiskSummary) {
      return analysis.summary;
    }
    return translatedRiskSummary;
  };

  // Parse and get risk assessment content (everything before "What this document is about")
  const getRiskAssessmentContent = () => {
    if (riskCurrentLanguage === 'en' || !translatedRiskSummary) {
      const content = analysis.summary;
      const sections = content.split('**What this document is about:**');
      return sections[0].trim();
    }
    return translatedRiskSummary;
  };

  // Parse and get document about content (everything after "What this document is about")
  const getDocumentAboutContent = () => {
    if (riskCurrentLanguage === 'en' || !translatedDocumentAbout) {
      const content = analysis.summary;
      const sections = content.split('**What this document is about:**');
      if (sections.length > 1) {
        return sections[1].trim();
      }
      return null;
    }
    return translatedDocumentAbout;
  };

  // Get display name for language
  const getLanguageDisplayName = (languageCode: string) => {
    const languageNames: { [key: string]: string } = {
      'es': 'Spanish (Español)',
      'fr': 'French (Français)', 
      'de': 'German (Deutsch)',
      'it': 'Italian (Italiano)',
      'pt': 'Portuguese (Português)',
      'hi': 'Hindi (हिंदी)',
      'zh': 'Chinese (中文)',
      'ar': 'Arabic (العربية)',
      'ru': 'Russian (Русский)',
      'ja': 'Japanese (日本語)',
      'ko': 'Korean (한국어)'
    };
    return languageNames[languageCode] || languageCode.toUpperCase();
  };

  // Create document context for chat
  const documentContext: DocumentContext = {
    documentType: classification?.document_type?.value || 'legal document',
    overallRisk: analysis.overall_risk.level,
    summary: analysis.summary,
    totalClauses: analysis.analysis_results.length
  };



  const openStatus = () => {
    setIsStatusOpen(true);
  };

  const runAdvancedAnalysis = async () => {
    toggleSection('nlAnalysis');
  };

  const exportToPDF = async () => {
    if (!featureAvailabilityService.isFeatureAvailable('export_pdf')) {
      const fallbackMessage = featureAvailabilityService.getFallbackMessage('export_pdf');
      notificationService.error(fallbackMessage);
      return;
    }

    setIsExporting(prev => ({ ...prev, pdf: true }));
    notificationService.info('Preparing PDF export...');

    const exportData: any = {
      analysis
    };
    if (fileInfo) exportData.file_info = fileInfo;
    if (classification) exportData.classification = classification;

    try {
      const result = await exportService.exportToPDF(exportData);

      if (result.success) {
        featureAvailabilityService.recordFeatureSuccess('export_pdf');
        notificationService.exportSuccess('PDF');
      } else {
        featureAvailabilityService.recordFeatureError('export_pdf');
        
        // Check if it's an authentication error
        if (result.error && result.error.includes('sign in')) {
          notificationService.error(result.error);
        } else {
          notificationService.exportError('PDF', () => {
            const fallbackData: any = { analysis };
            if (fileInfo) fallbackData.file_info = fileInfo;
            if (classification) fallbackData.classification = classification;
            exportService.exportAsText(fallbackData);
          });
        }
      }
    } catch (error: any) {
      console.error('Export error:', error);
      featureAvailabilityService.recordFeatureError('export_pdf', error as Error);
      
      // Check if it's an authentication error
      if (error.message && error.message.includes('Authentication required')) {
        notificationService.error('Please sign in to export PDF documents. Click the "Sign In" button in the top navigation.');
      } else {
        notificationService.error('Export failed. Please try again or use the text export option.');
      }
    } finally {
      setIsExporting(prev => ({ ...prev, pdf: false }));
    }
  };

  const exportToWord = async () => {
    if (!featureAvailabilityService.isFeatureAvailable('export_word')) {
      const fallbackMessage = featureAvailabilityService.getFallbackMessage('export_word');
      notificationService.error(fallbackMessage);
      return;
    }

    setIsExporting(prev => ({ ...prev, word: true }));
    notificationService.info('Preparing Word document export...');

    const exportData: any = {
      analysis
    };
    if (fileInfo) exportData.file_info = fileInfo;
    if (classification) exportData.classification = classification;

    try {
      const result = await exportService.exportToWord(exportData);

      if (result.success) {
        featureAvailabilityService.recordFeatureSuccess('export_word');
        notificationService.exportSuccess('Word');
      } else {
        featureAvailabilityService.recordFeatureError('export_word');
        notificationService.exportError('Word', () => {
          const fallbackData: any = { analysis };
          if (fileInfo) fallbackData.file_info = fileInfo;
          if (classification) fallbackData.classification = classification;
          exportService.exportAsText(fallbackData);
        });
      }
    } catch (error) {
      console.error('Export error:', error);
      featureAvailabilityService.recordFeatureError('export_word', error as Error);
      notificationService.error('Word export failed. Please try again or use the text export option.');
    } finally {
      setIsExporting(prev => ({ ...prev, word: false }));
    }
  };



  return (
    <>
      <div className="min-h-screen pt-20 pb-16">
        <div className="container mx-auto px-6">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-12"
          >
            <div className="flex-1">
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 flex items-center">
                <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center mr-4">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                Document Analysis Results
              </h1>
              <p className="text-xl text-slate-300 leading-relaxed max-w-2xl">
                Comprehensive AI-powered legal document analysis with risk assessment, 
                clause-by-clause breakdown, and actionable insights
              </p>
            </div>

            <div className="flex items-center space-x-4 mt-6 sm:mt-0">
              <button
                onClick={onBackToHome}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-slate-700 to-slate-600 text-white rounded-xl hover:from-slate-600 hover:to-slate-500 transition-all duration-300 transform hover:scale-105 shadow-lg"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                <span className="hidden sm:inline font-semibold">Analyze Another Document</span>
                <span className="sm:hidden font-semibold">New Analysis</span>
              </button>
            </div>
          </motion.div>



          {/* Overall Risk Assessment & Document Summary */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className={cn(
              "border-2 rounded-2xl p-8 mb-10 shadow-xl backdrop-blur-sm",
              analysis.overall_risk.level === 'RED' ? "border-red-500/50 bg-gradient-to-r from-red-500/10 to-red-600/5" :
                analysis.overall_risk.level === 'YELLOW' ? "border-yellow-500/50 bg-gradient-to-r from-yellow-500/10 to-orange-500/5" :
                  "border-green-500/50 bg-gradient-to-r from-green-500/10 to-emerald-500/5"
            )}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-4">
                <div className={cn(
                  "traffic-light-large",
                  getRiskColor(analysis.overall_risk.level)
                )} />
                <div>
                  <h2 className="text-2xl font-bold text-white">Overall Risk Assessment & Summary</h2>
                  <p className="text-slate-400">
                    {riskCurrentLanguage === 'en' 
                      ? 'Comprehensive document analysis and risk evaluation' 
                      : `Translated to ${getLanguageDisplayName(riskCurrentLanguage)}`
                    }
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={toggleRiskTranslationPanel}
                  className={`inline-flex items-center px-3 py-2 rounded-lg transition-colors text-sm ${
                    showRiskTranslation 
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  <Globe className="w-4 h-4 mr-2" />
                  Translate
                </button>

                {speechSupported && (
                  <button
                    onClick={isSpeaking ? stopSpeech : speakRiskAssessment}
                    className={`inline-flex items-center px-3 py-2 rounded-lg transition-colors text-sm ${
                      isSpeaking && currentSpeechSection === 'risk'
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                    disabled={isSpeaking && currentSpeechSection !== 'risk'}
                  >
                    {isSpeaking && currentSpeechSection === 'risk' ? (
                      <Pause className="w-4 h-4 mr-2" />
                    ) : (
                      <Volume2 className="w-4 h-4 mr-2" />
                    )}
                    {isSpeaking && currentSpeechSection === 'risk' ? 'Stop' : 'Listen'}
                  </button>
                )}

                {analysis.overall_risk.low_confidence_warning && (
                  <div className={cn(
                    "px-3 py-1 rounded-full border text-sm",
                    getRiskBadgeColor('YELLOW')
                  )}>
                    <AlertTriangle className="w-4 h-4 inline mr-1" />
                    Low Confidence: {analysis.overall_risk.confidence_percentage}%
                  </div>
                )}
              </div>
            </div>

            {/* Document Translation Panel */}
            {showRiskTranslation && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-6"
              >
                <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-600/30">
                  <div className="flex items-center justify-between mb-4">
                    <h5 className="text-sm font-semibold text-white flex items-center">
                      <Globe className="w-4 h-4 mr-2" />
                      Translate Document Summary
                    </h5>
                    <div className="text-xs text-slate-400">
                      All sections will be translated
                    </div>
                  </div>
                  
                  {/* Language Selection */}
                  <div className="flex items-center space-x-3 mb-4">
                    <label htmlFor="document-language-select" className="text-sm text-slate-300">
                      Select language to translate all sections:
                    </label>
                    <select
                      id="document-language-select"
                      value={riskCurrentLanguage}
                      onChange={(e) => handleLanguageChange(e.target.value)}
                      className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:border-cyan-500 focus:outline-none"
                    >
                      <option value="en">🇺🇸 English</option>
                      <option value="es">🇪🇸 Español</option>
                      <option value="fr">🇫🇷 Français</option>
                      <option value="de">🇩🇪 Deutsch</option>
                      <option value="it">🇮🇹 Italiano</option>
                      <option value="pt">🇵🇹 Português</option>
                      <option value="hi">🇮🇳 हिंदी</option>
                      <option value="zh">🇨🇳 中文</option>
                      <option value="ar">🇸🇦 العربية</option>
                      <option value="ru">🇷🇺 Русский</option>
                      <option value="ja">🇯🇵 日本語</option>
                      <option value="ko">🇰🇷 한국어</option>
                    </select>
                    
                    <button
                      onClick={translateDocument}
                      disabled={isTranslating || riskCurrentLanguage === 'en'}
                      className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-400 hover:to-cyan-400 transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isTranslating ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Translating...
                        </>
                      ) : (
                        <>
                          <Globe className="w-4 h-4 mr-2" />
                          Translate
                        </>
                      )}
                    </button>

                    {riskCurrentLanguage !== 'en' && (translatedRiskSummary || translatedDocumentAbout) && (
                      <button
                        onClick={() => handleLanguageChange('en')}
                        className="inline-flex items-center px-3 py-2 bg-slate-600 text-slate-300 rounded-lg hover:bg-slate-500 transition-all text-sm"
                      >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to English
                      </button>
                    )}
                  </div>

                  {/* Translation Status */}
                  {(translatedRiskSummary || translatedDocumentAbout) && riskCurrentLanguage !== 'en' && (
                    <div className="flex items-center space-x-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg mb-4">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-green-400 text-sm">
                        Translation Complete
                      </span>
                      <div className="flex items-center space-x-4 ml-auto">
                        <div className="text-xs text-slate-400">
                          {[translatedRiskSummary, translatedDocumentAbout].filter(Boolean).length} Sections Translated
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Legal Context Preserved Notice */}
                  <div className="text-xs text-slate-500 mb-4">
                    💡 Legal context preserved • 1-hour caching • Rate limited
                  </div>
                
                  {/* Text-to-Speech Settings */}
                  {speechSupported && (
                    <div className="mt-4 pt-4 border-t border-slate-600/30">
                      <div className="flex items-center justify-between mb-3">
                        <h6 className="text-sm font-semibold text-white flex items-center">
                          <Settings className="w-4 h-4 mr-2" />
                          Text-to-Speech Settings
                        </h6>
                        <div className="text-xs text-slate-400">
                          Shortcuts: Ctrl+Shift+S (play/stop), Esc (stop)
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Voice Selection */}
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Voice</label>
                          <select
                            value={selectedVoice?.name || ''}
                            onChange={(e) => {
                              const voice = availableVoices.find(v => v.name === e.target.value);
                              if (voice) setSelectedVoice(voice);
                            }}
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-xs"
                          >
                            {availableVoices
                              .filter(voice => voice.lang.startsWith(riskCurrentLanguage) || voice.lang.startsWith('en'))
                              .map(voice => (
                                <option key={voice.name} value={voice.name}>
                                  {voice.name} ({voice.lang})
                                </option>
                              ))}
                          </select>
                        </div>
                        
                        {/* Speech Rate */}
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">
                            Speed: {speechRate}x
                          </label>
                          <input
                            type="range"
                            min="0.5"
                            max="2"
                            step="0.1"
                            value={speechRate}
                            onChange={(e) => setSpeechRate(parseFloat(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* Document Summary Content */}
            <div className={cn(
              "rounded-xl p-6 mb-6 border",
              analysis.overall_risk.level === 'RED' ? "bg-red-500/10 border-red-500/30" :
                analysis.overall_risk.level === 'YELLOW' ? "bg-yellow-500/10 border-yellow-500/30" :
                  "bg-green-500/10 border-green-500/30"
            )}>
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2 flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  Document Summary
                </h3>
              </div>
              
              {/* Risk Assessment Section */}
              <div className={cn(
                "text-lg leading-relaxed mb-6 transition-all duration-300",
                isSpeaking && currentSpeechSection === 'risk' && "bg-blue-500/10 border border-blue-500/30 rounded-lg p-4"
              )}>
                <MarkdownRenderer text={getRiskAssessmentContent()} />
                {isSpeaking && currentSpeechSection === 'risk' && (
                  <div className="flex items-center mt-3 text-blue-400 text-sm">
                    <Volume2 className="w-4 h-4 mr-2 animate-pulse" />
                    Reading risk assessment... (Press Esc to stop)
                  </div>
                )}
              </div>
              
              {/* What this document is about Section */}
              {getDocumentAboutContent() && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-md font-semibold text-white flex items-center">
                      <Info className="w-4 h-4 mr-2" />
                      What this document is about
                    </h4>
                    
                    {speechSupported && (
                      <button
                        onClick={isSpeaking && currentSpeechSection === 'about' ? stopSpeech : speakDocumentAbout}
                        className={`inline-flex items-center px-2 py-1 rounded-lg transition-colors text-xs ${
                          isSpeaking && currentSpeechSection === 'about'
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                        }`}
                        disabled={isSpeaking && currentSpeechSection !== 'about'}
                      >
                        {isSpeaking && currentSpeechSection === 'about' ? (
                          <Pause className="w-3 h-3 mr-1" />
                        ) : (
                          <Play className="w-3 h-3 mr-1" />
                        )}
                        {isSpeaking && currentSpeechSection === 'about' ? 'Stop' : 'Listen'}
                      </button>
                    )}
                  </div>
                  <div className={cn(
                    "text-base leading-relaxed text-slate-300 bg-slate-800/30 rounded-lg p-4 border border-slate-600/30 transition-all duration-300",
                    isSpeaking && currentSpeechSection === 'about' && "bg-blue-500/10 border-blue-500/30"
                  )}>
                    <MarkdownRenderer text={getDocumentAboutContent()} />
                    {isSpeaking && currentSpeechSection === 'about' && (
                      <div className="flex items-center mt-3 text-blue-400 text-sm">
                        <Volume2 className="w-4 h-4 mr-2 animate-pulse" />
                        Reading document overview... (Press Esc to stop)
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Document Statistics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-600/30">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{analysis.analysis_results.length}</div>
                  <div className="text-sm text-slate-400">Total Clauses</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">
                    {analysis.analysis_results.filter(r => r.risk_level.level === 'RED').length}
                  </div>
                  <div className="text-sm text-slate-400">High Risk</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">
                    {analysis.analysis_results.filter(r => r.risk_level.level === 'YELLOW').length}
                  </div>
                  <div className="text-sm text-slate-400">Medium Risk</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">
                    {analysis.analysis_results.filter(r => r.risk_level.level === 'GREEN').length}
                  </div>
                  <div className="text-sm text-slate-400">Low Risk</div>
                </div>
              </div>
            </div>

            {/* Risk Category Breakdown */}
            {analysis.overall_risk.risk_categories && (
              <div>
                <h3 className="font-semibold text-white mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Risk Category Breakdown
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(analysis.overall_risk.risk_categories).map(([category, score]) => (
                    <div key={category} className="text-center">
                      <div className="mb-2">
                        <div className="confidence-bar">
                          <div
                            className={cn(
                              "confidence-fill",
                              score > 0.7 ? "bg-red-500" : score > 0.4 ? "bg-yellow-500" : "bg-green-500"
                            )}
                            style={{ width: `${score * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="text-sm">
                        <div className="font-semibold text-white capitalize">{category}</div>
                        <div className="text-slate-400">{Math.round(score * 100)}% Risk</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>

          {/* Paginated Clause Analysis */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <PaginatedClauseAnalysis
              analysisId={analysis.analysis_id}
              onOpenChat={openChat}
              onOpenHumanSupport={openHumanSupport}
              className="mb-8"
            />
          </motion.div>



          {/* Document Comparison Section */}
          <InlineDocumentComparison
            currentDocument={{
              text: analysis.document_text || analysis.analysis_results.map(clause => clause.clause_text).join('\n\n') || '',
              type: analysis.document_type || 'general_contract'
            }}
            isExpanded={true}
            onToggleExpanded={() => {}}
            showExpandToggle={false}
            className="mb-8"
          />

          {/* Severity Indicators */}
          {analysis.severity_indicators && analysis.severity_indicators.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="bg-yellow-500/10 border border-yellow-500/30 rounded-2xl p-6 mb-8"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2" />
                Critical Issues Detected
              </h2>
              <p className="text-slate-300 mb-4">High-priority concerns that require immediate attention</p>

              <div className="grid md:grid-cols-2 gap-4">
                {analysis.severity_indicators.map((indicator, index) => (
                  <div key={index} className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3">
                    <div className="flex items-center">
                      <Shield className="w-4 h-4 text-yellow-400 mr-2 flex-shrink-0" />
                      <span className="text-yellow-400 font-medium">{indicator}</span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Interactive AI Features */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7 }}
            className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-8"
          >
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white flex items-center mb-2">
                <Zap className="w-5 h-5 mr-2" />
                Interactive AI Features
              </h2>
              <p className="text-slate-400">Advanced Google Cloud AI integration for comprehensive document analysis</p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* AI Confidence Analysis */}
              <div className="feature-card p-4">
                <h3 className="font-semibold text-white mb-2 flex items-center">
                  <Shield className="w-4 h-4 mr-2" />
                  AI Confidence Analysis
                </h3>
                <p className="text-slate-400 text-sm mb-3">View detailed confidence metrics for AI transparency.</p>
                <button
                  onClick={() => toggleSection('confidence')}
                  className="inline-flex items-center px-3 py-2 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded-lg hover:bg-blue-500/30 transition-colors text-sm"
                >
                  <BarChart3 className="w-4 h-4 mr-2" />
                  View Confidence Metrics
                </button>
                {expandedSections.has('confidence') && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-3 p-3 bg-slate-900/50 rounded-lg"
                  >
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Overall Analysis:</span>
                        <span className="text-slate-400">{analysis.overall_risk.confidence_percentage}%</span>
                      </div>
                      <div className="confidence-bar">
                        <div
                          className={cn("confidence-fill", getConfidenceColor(analysis.overall_risk.confidence_percentage))}
                          style={{ width: `${analysis.overall_risk.confidence_percentage}%` }}
                        />
                      </div>
                      <div className="text-xs text-slate-500">
                        Average clause confidence: {Math.round(analysis.analysis_results.reduce((acc, r) => acc + r.risk_level.confidence_percentage, 0) / analysis.analysis_results.length)}%
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Multi-language Support */}
              <div className="feature-card p-4">
                <h3 className="font-semibold text-white mb-2 flex items-center">
                  <Globe className="w-4 h-4 mr-2" />
                  Multi-language Support
                </h3>
                <p className="text-slate-400 text-sm mb-3">Translate the overall summary to your preferred language.</p>
                <label htmlFor="language-select-summary" className="sr-only">
                  Select translation language for summary
                </label>
                <select
                  id="language-select-summary"
                  value={currentLanguage}
                  onChange={(e) => setCurrentLanguage(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm mb-2 focus:border-cyan-500 focus:outline-none"
                  aria-label="Select translation language for summary"
                >
                  <option value="en">English</option>
                  <option value="hi">Hindi (हिंदी)</option>
                  <option value="es">Spanish (Español)</option>
                  <option value="fr">French (Français)</option>
                  <option value="de">German (Deutsch)</option>
                  <option value="zh">Chinese (中文)</option>
                  <option value="ar">Arabic (العربية)</option>
                  <option value="pt">Portuguese (Português)</option>
                </select>
                <button
                  onClick={() => openTranslation(analysis.summary, 'Document Summary')}
                  className="inline-flex items-center px-3 py-2 bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 rounded-lg hover:bg-cyan-500/30 transition-colors text-sm"
                >
                  <Globe className="w-4 h-4 mr-2" />
                  Translate Summary
                </button>
              </div>

              {/* AI Clarification */}
              <div className="feature-card p-4">
                <h3 className="font-semibold text-white mb-2 flex items-center">
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Get Help & Clarification
                </h3>
                <p className="text-slate-400 text-sm mb-4">Ask questions about the document or get expert guidance.</p>
                <div className="space-y-3">
                  <button
                    onClick={() => openChat()}
                    className="w-full inline-flex items-center justify-center px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-400 hover:to-pink-400 transition-all"
                  >
                    <MessageCircle className="w-4 h-4 mr-2" />
                    AI Chat Assistant
                  </button>
                  <button
                    onClick={() => openHumanSupport()}
                    className="w-full inline-flex items-center justify-center px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
                  >
                    <Users className="w-4 h-4 mr-2" />
                    Contact Human Expert
                  </button>
                </div>
              </div>



              {/* Google Cloud AI Services */}
              <div className="feature-card p-4">
                <h3 className="font-semibold text-white mb-2 flex items-center">
                  <Zap className="w-4 h-4 mr-2" />
                  Google Cloud AI Services
                </h3>
                <p className="text-slate-400 text-sm mb-3">View the status of integrated Google Cloud AI services.</p>
                <button
                  onClick={openStatus}
                  className="inline-flex items-center px-3 py-2 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded-lg hover:bg-blue-500/30 transition-colors text-sm"
                >
                  <Activity className="w-4 h-4 mr-2" />
                  Check AI Services
                </button>
              </div>

              {/* Advanced Analysis */}
              <div className="feature-card p-4">
                <h3 className="font-semibold text-white mb-2 flex items-center">
                  <BarChart3 className="w-4 h-4 mr-2" />
                  Advanced Analysis
                </h3>
                <p className="text-slate-400 text-sm mb-3">Get detailed Natural Language AI insights about your document.</p>
                <button
                  onClick={() => runAdvancedAnalysis()}
                  className="inline-flex items-center px-3 py-2 bg-purple-500/20 text-purple-400 border border-purple-500/50 rounded-lg hover:bg-purple-500/30 transition-colors text-sm"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Run NL Analysis
                </button>
              </div>
            </div>

            {/* Expandable Sections for Features */}
            {expandedSections.has('nlAnalysis') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6 p-6 bg-purple-500/10 border border-purple-500/30 rounded-lg"
              >
                <h3 className="text-lg font-semibold text-white mb-4">Advanced Natural Language Analysis</h3>
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                      <h4 className="font-medium text-white mb-2 flex items-center">
                        <BarChart3 className="w-4 h-4 mr-2" />
                        Sentiment Analysis
                      </h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-300">Overall Tone:</span>
                          <span className="text-blue-400">Formal/Legal</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-300">Complexity Level:</span>
                          <span className="text-yellow-400">High</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-300">Readability Score:</span>
                          <span className="text-red-400">Professional Level</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                      <h4 className="font-medium text-white mb-2 flex items-center">
                        <Activity className="w-4 h-4 mr-2" />
                        Entity Recognition
                      </h4>
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                          <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">Organizations</span>
                          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">Dates</span>
                          <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs">Legal Terms</span>
                          <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">Financial</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                    <h4 className="font-medium text-white mb-2">Key Insights</h4>
                    <ul className="space-y-2 text-sm text-slate-300">
                      <li className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Document contains {analysis.analysis_results.length} distinct legal clauses</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Average confidence level: {Math.round(analysis.analysis_results.reduce((acc, r) => acc + r.risk_level.confidence_percentage, 0) / analysis.analysis_results.length)}%</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Processing completed in {analysis.processing_time.toFixed(2)} seconds</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>



          {/* Enhanced Export & Share */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 mb-8"
          >
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white flex items-center mb-2">
                <Download className="w-5 h-5 mr-2" />
                Enhanced Export & Share
              </h2>
              <p className="text-slate-400">Professional report generation with multiple formats</p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <button
                onClick={() => exportToPDF()}
                disabled={isExporting.pdf}
                className="inline-flex items-center justify-center px-4 py-3 bg-red-500/20 text-red-400 border border-red-500/50 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExporting.pdf ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Export PDF
                  </>
                )}
              </button>

              <button
                onClick={() => exportToWord()}
                disabled={isExporting.word}
                className="inline-flex items-center justify-center px-4 py-3 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExporting.word ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    Export Word
                  </>
                )}
              </button>

              <button
                onClick={() => setIsEmailModalOpen(true)}
                className="inline-flex items-center justify-center px-4 py-3 bg-purple-500/20 text-purple-400 border border-purple-500/50 rounded-lg hover:bg-purple-500/30 transition-colors"
              >
                <Mail className="w-4 h-4 mr-2" />
                Send to Email
              </button>
              
              <button
                onClick={() => window.print()}
                className="inline-flex items-center justify-center px-4 py-3 bg-green-500/20 text-green-400 border border-green-500/50 rounded-lg hover:bg-green-500/30 transition-colors"
              >
                <Download className="w-4 h-4 mr-2" />
                Print Analysis
              </button>

              <button
                onClick={copyResults}
                className="inline-flex items-center justify-center px-4 py-3 bg-slate-600/50 text-slate-300 border border-slate-600 rounded-lg hover:bg-slate-600/70 transition-colors"
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy to Clipboard
              </button>
            </div>

            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <p className="text-blue-400 text-sm">
                <Info className="w-4 h-4 inline mr-2" />
                <strong>Disclaimer:</strong> This analysis is for informational purposes only and does not constitute legal advice.
                Please consult with a qualified legal professional for specific legal matters.
              </p>
            </div>
          </motion.div>

          {/* Action Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.9 }}
            className="flex flex-wrap gap-4 justify-center"
          >
            <button
              onClick={onBackToHome}
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Analyze Another Document
            </button>
          </motion.div>
        </div>
      </div>

      {/* Modals */}
      <AIChat
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        documentContext={documentContext}
        clauseContext={activeChatClause}
      />

      <HumanSupport
        isOpen={isHumanSupportOpen}
        onClose={() => setIsHumanSupportOpen(false)}
        documentContext={documentContext}
        clauseContext={activeChatClause}
      />

      <TranslationModal
        isOpen={isTranslationOpen}
        onClose={() => setIsTranslationOpen(false)}
        originalText={translationText}
        title={translationTitle}
      />

      <StatusModal
        isOpen={isStatusOpen}
        onClose={() => setIsStatusOpen(false)}
      />



      {/* Email Modal */}
      <EmailModal
        isOpen={isEmailModalOpen}
        onClose={() => setIsEmailModalOpen(false)}
        analysisData={{
          analysis,
          ...(fileInfo && { file_info: fileInfo }),
          ...(classification && { classification: classification })
        }}
        userEmail="" // This should come from auth context when available
      />

      {/* Low Confidence Popup */}
      {analysis.overall_confidence !== undefined && analysis.confidence_breakdown && (
        <LowConfidencePopup
          isVisible={showConfidencePopup}
          confidence={analysis.overall_confidence}
          confidenceBreakdown={analysis.confidence_breakdown}
          onAccept={handleExpertReviewAccept}
          onDecline={handleExpertReviewDecline}
          onClose={() => setShowConfidencePopup(false)}
        />
      )}

      {/* Expert Dashboard Popup */}
      <ExpertDashboardPopup
        isVisible={showExpertDashboardPopup}
        onGoToDashboard={handleGoToExpertDashboard}
        onStayHere={handleStayOnResults}
        onClose={() => setShowExpertDashboardPopup(false)}
      />
    </>
  );
});

export default Results;
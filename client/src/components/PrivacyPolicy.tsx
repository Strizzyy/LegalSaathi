import { motion } from 'framer-motion';
import { Shield, ArrowLeft, Eye, Lock, Database, UserCheck } from 'lucide-react';

interface PrivacyPolicyProps {
  onClose?: () => void;
}

export function PrivacyPolicy({ onClose }: PrivacyPolicyProps) {
  return (
    <div className="min-h-screen bg-slate-900 text-white py-20">
      <div className="container mx-auto px-6 max-w-4xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          {onClose && (
            <button
              onClick={onClose}
              className="flex items-center space-x-2 text-cyan-400 hover:text-cyan-300 transition-colors mb-6"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          )}
          
          <div className="flex items-center space-x-4 mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-white">Privacy Policy</h1>
              <p className="text-slate-400 text-lg">Last updated: January 2025</p>
            </div>
          </div>
          
          <p className="text-slate-300 text-lg leading-relaxed">
            At LegalSaathi, we are committed to protecting your privacy and ensuring the security of your personal information. 
            This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI-powered legal document analysis service.
          </p>
        </motion.div>

        {/* Content Sections */}
        <div className="space-y-12">
          {/* Information We Collect */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Eye className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">1. Information We Collect</h2>
            </div>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">1.1 Personal Information</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Email address (for account creation and communication)</li>
                  <li>• Name (optional, for personalization)</li>
                  <li>• Authentication data (encrypted passwords, OAuth tokens)</li>
                  <li>• Profile preferences and settings</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">1.2 Document Data</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Legal documents you upload for analysis (temporarily processed)</li>
                  <li>• Document metadata (file size, type, upload timestamp)</li>
                  <li>• Analysis results and generated insights</li>
                  <li>• User interactions with analysis results</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">1.3 Technical Information</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• IP address and device information</li>
                  <li>• Browser type and version</li>
                  <li>• Usage patterns and feature interactions</li>
                  <li>• Error logs and performance metrics</li>
                </ul>
              </div>
            </div>
          </motion.section>

          {/* How We Use Information */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Database className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">2. How We Use Your Information</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">2.1 Service Provision</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Analyze legal documents using AI technology</li>
                  <li>• Generate risk assessments and clause analysis</li>
                  <li>• Provide document summaries and translations</li>
                  <li>• Deliver personalized insights based on experience level</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">2.2 Service Improvement</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Enhance AI model accuracy and performance</li>
                  <li>• Develop new features and capabilities</li>
                  <li>• Monitor system performance and reliability</li>
                  <li>• Conduct security and fraud prevention</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">2.3 Communication</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Send analysis results and notifications</li>
                  <li>• Provide customer support and assistance</li>
                  <li>• Share important service updates</li>
                  <li>• Respond to inquiries and feedback</li>
                </ul>
              </div>
            </div>
          </motion.section>

          {/* Data Security */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Lock className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">3. Data Security and Protection</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">3.1 Security Measures</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• End-to-end encryption for data transmission</li>
                  <li>• Secure cloud infrastructure with Google Cloud Platform</li>
                  <li>• Regular security audits and vulnerability assessments</li>
                  <li>• Access controls and authentication protocols</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">3.2 Document Handling</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Documents are processed temporarily and not permanently stored</li>
                  <li>• Automatic deletion of uploaded files after analysis completion</li>
                  <li>• Analysis results stored securely with user consent</li>
                  <li>• No sharing of document content with third parties</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">3.3 Data Retention</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• User account data retained while account is active</li>
                  <li>• Analysis history stored for user convenience (can be deleted)</li>
                  <li>• Technical logs retained for 90 days for security purposes</li>
                  <li>• Immediate deletion upon account termination request</li>
                </ul>
              </div>
            </div>
          </motion.section>

          {/* User Rights */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <UserCheck className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">4. Your Rights and Choices</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">4.1 Access and Control</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Access and review your personal information</li>
                  <li>• Update or correct your account details</li>
                  <li>• Download your analysis history</li>
                  <li>• Delete specific analysis results</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">4.2 Data Portability</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Export your data in standard formats</li>
                  <li>• Transfer analysis results to other services</li>
                  <li>• Receive copies of your information upon request</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">4.3 Account Deletion</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Request complete account deletion at any time</li>
                  <li>• All personal data removed within 30 days</li>
                  <li>• Confirmation provided upon completion</li>
                </ul>
              </div>
            </div>
          </motion.section>

          {/* Third Party Services */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Shield className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">5. Third-Party Services</h2>
            </div>
            
            <div className="space-y-4 text-slate-300">
              <p>
                LegalSaathi integrates with trusted third-party services to provide our functionality:
              </p>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">5.1 Google Cloud Platform</h3>
                <ul className="space-y-2 ml-4">
                  <li>• Document AI for text extraction and processing</li>
                  <li>• Natural Language API for content analysis</li>
                  <li>• Translation API for multi-language support</li>
                  <li>• Speech-to-Text for voice input features</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">5.2 Firebase Authentication</h3>
                <ul className="space-y-2 ml-4">
                  <li>• Secure user authentication and account management</li>
                  <li>• OAuth integration with Google and other providers</li>
                  <li>• Session management and security</li>
                </ul>
              </div>
              
              <p className="text-sm text-slate-400 mt-4">
                These services operate under their own privacy policies. We ensure all integrations 
                meet our security and privacy standards.
              </p>
            </div>
          </motion.section>

          {/* Contact Information */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-xl p-8 border border-cyan-500/20"
          >
            <h2 className="text-2xl font-semibold text-white mb-6">6. Contact Us</h2>
            
            <div className="space-y-4 text-slate-300">
              <p>
                If you have any questions about this Privacy Policy or our data practices, please contact us:
              </p>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-cyan-300 mb-2">General Inquiries</h3>
                  <p>Email: privacy@legalsaathi.com</p>
                  <p>Response time: Within 48 hours</p>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-cyan-300 mb-2">Data Protection Officer</h3>
                  <p>Email: dpo@legalsaathi.com</p>
                  <p>For data protection and privacy concerns</p>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-slate-800/50 rounded-lg">
                <p className="text-sm text-slate-400">
                  <strong>Important:</strong> This Privacy Policy may be updated periodically to reflect 
                  changes in our practices or legal requirements. We will notify users of significant 
                  changes via email or through our service notifications.
                </p>
              </div>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
}
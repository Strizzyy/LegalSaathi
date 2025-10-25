import { motion } from 'framer-motion';
import { FileText, ArrowLeft, AlertTriangle, Scale, Users, Gavel } from 'lucide-react';

interface TermsOfServiceProps {
  onClose?: () => void;
}

export function TermsOfService({ onClose }: TermsOfServiceProps) {
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
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-white">Terms of Service</h1>
              <p className="text-slate-400 text-lg">Last updated: January 2025</p>
            </div>
          </div>
          
          <p className="text-slate-300 text-lg leading-relaxed">
            Welcome to LegalSaathi. These Terms of Service ("Terms") govern your use of our AI-powered legal document analysis platform. 
            By accessing or using our service, you agree to be bound by these Terms.
          </p>
        </motion.div>

        {/* Important Disclaimer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6 mb-8"
        >
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-6 h-6 text-amber-400 mt-1 flex-shrink-0" />
            <div>
              <h3 className="text-lg font-semibold text-amber-300 mb-2">Important Legal Disclaimer</h3>
              <p className="text-amber-100 text-sm leading-relaxed">
                LegalSaathi provides informational analysis only and does not constitute legal advice. 
                Our AI-powered insights are for educational and informational purposes. Always consult 
                with a qualified legal professional for specific legal matters and decisions.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Content Sections */}
        <div className="space-y-12">
          {/* Acceptance of Terms */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Scale className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">1. Acceptance of Terms</h2>
            </div>
            
            <div className="space-y-4 text-slate-300">
              <p>
                By creating an account, uploading documents, or using any features of LegalSaathi, you acknowledge that:
              </p>
              
              <ul className="space-y-2 ml-4">
                <li>• You have read, understood, and agree to these Terms of Service</li>
                <li>• You are at least 18 years old or have parental/guardian consent</li>
                <li>• You have the legal capacity to enter into this agreement</li>
                <li>• You will use the service in compliance with all applicable laws</li>
              </ul>
              
              <p className="text-sm text-slate-400 mt-4">
                If you do not agree to these terms, please do not use our service.
              </p>
            </div>
          </motion.section>

          {/* Service Description */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <FileText className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">2. Service Description</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">2.1 What We Provide</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• AI-powered analysis of legal documents</li>
                  <li>• Risk assessment and clause identification</li>
                  <li>• Document summarization and translation services</li>
                  <li>• Educational insights about legal terms and implications</li>
                  <li>• Document comparison and compliance checking</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">2.2 Service Limitations</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Analysis results are informational and not legally binding</li>
                  <li>• AI models may have limitations in accuracy or completeness</li>
                  <li>• Service availability may vary due to maintenance or technical issues</li>
                  <li>• Some features may require user authentication</li>
                </ul>
              </div>
            </div>
          </motion.section>

          {/* User Responsibilities */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Users className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">3. User Responsibilities</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">3.1 Account Security</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Maintain the confidentiality of your account credentials</li>
                  <li>• Notify us immediately of any unauthorized access</li>
                  <li>• Use strong passwords and enable two-factor authentication when available</li>
                  <li>• You are responsible for all activities under your account</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">3.2 Acceptable Use</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Upload only documents you have the right to analyze</li>
                  <li>• Do not upload confidential or privileged attorney-client communications</li>
                  <li>• Respect intellectual property rights of others</li>
                  <li>• Do not attempt to reverse engineer or exploit our AI models</li>
                  <li>• Do not use the service for illegal or harmful purposes</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">3.3 Prohibited Activities</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• Uploading malicious files, viruses, or harmful code</li>
                  <li>• Attempting to gain unauthorized access to our systems</li>
                  <li>• Sharing analysis results that contain others' confidential information</li>
                  <li>• Using automated tools to scrape or abuse our service</li>
                  <li>• Impersonating others or providing false information</li>
                </ul>
              </div>
            </div>
          </motion.section>

          {/* Intellectual Property */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Gavel className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">4. Intellectual Property</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">4.1 Our Rights</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• LegalSaathi owns all rights to our platform, AI models, and technology</li>
                  <li>• Our trademarks, logos, and branding are protected intellectual property</li>
                  <li>• Analysis algorithms and methodologies are proprietary</li>
                  <li>• User interface design and user experience elements are copyrighted</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">4.2 Your Rights</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• You retain ownership of documents you upload</li>
                  <li>• You own the analysis results generated for your documents</li>
                  <li>• You may download and use your analysis results as needed</li>
                  <li>• You grant us limited rights to process your documents for analysis</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">4.3 License Grant</h3>
                <p className="text-slate-300">
                  We grant you a limited, non-exclusive, non-transferable license to use LegalSaathi 
                  for your personal or business legal document analysis needs, subject to these Terms.
                </p>
              </div>
            </div>
          </motion.section>

          {/* Disclaimers and Limitations */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <AlertTriangle className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">5. Disclaimers and Limitations</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">5.1 Service Disclaimers</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• LegalSaathi is provided "as is" without warranties of any kind</li>
                  <li>• We do not guarantee the accuracy or completeness of AI analysis</li>
                  <li>• Service availability and performance may vary</li>
                  <li>• We are not liable for decisions made based on our analysis</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">5.2 Limitation of Liability</h3>
                <div className="text-slate-300 space-y-2">
                  <p>
                    To the maximum extent permitted by law, LegalSaathi and its team members shall not be liable for:
                  </p>
                  <ul className="space-y-2 ml-4">
                    <li>• Any indirect, incidental, or consequential damages</li>
                    <li>• Loss of profits, data, or business opportunities</li>
                    <li>• Damages resulting from reliance on our analysis</li>
                    <li>• Any amount exceeding the fees paid for our service</li>
                  </ul>
                </div>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">5.3 Professional Legal Advice</h3>
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                  <p className="text-amber-100 text-sm">
                    <strong>Important:</strong> LegalSaathi does not provide legal advice. Our AI analysis 
                    is for informational purposes only. Always consult with qualified legal professionals 
                    for legal advice specific to your situation.
                  </p>
                </div>
              </div>
            </div>
          </motion.section>

          {/* Privacy and Data */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <FileText className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">6. Privacy and Data Handling</h2>
            </div>
            
            <div className="space-y-4 text-slate-300">
              <p>
                Your privacy is important to us. Our data handling practices are governed by our Privacy Policy, which includes:
              </p>
              
              <ul className="space-y-2 ml-4">
                <li>• Temporary processing of uploaded documents</li>
                <li>• Secure storage of analysis results</li>
                <li>• No permanent storage of document content</li>
                <li>• Encryption of data in transit and at rest</li>
                <li>• Compliance with applicable data protection laws</li>
              </ul>
              
              <p className="text-sm text-slate-400 mt-4">
                Please review our Privacy Policy for detailed information about how we collect, 
                use, and protect your information.
              </p>
            </div>
          </motion.section>

          {/* Termination */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="bg-slate-800/50 rounded-xl p-8 border border-slate-700"
          >
            <div className="flex items-center space-x-3 mb-6">
              <Users className="w-6 h-6 text-cyan-400" />
              <h2 className="text-2xl font-semibold text-white">7. Account Termination</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">7.1 Voluntary Termination</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• You may delete your account at any time</li>
                  <li>• Account deletion removes all personal data within 30 days</li>
                  <li>• Analysis history will be permanently deleted</li>
                  <li>• Some data may be retained for legal or security purposes</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-xl font-medium text-cyan-300 mb-3">7.2 Service Termination</h3>
                <ul className="text-slate-300 space-y-2 ml-4">
                  <li>• We may suspend or terminate accounts for Terms violations</li>
                  <li>• We may discontinue the service with reasonable notice</li>
                  <li>• Users will be notified of any service changes</li>
                  <li>• Data export options will be provided when possible</li>
                </ul>
              </div>
            </div>
          </motion.section>

          {/* Contact and Updates */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.9 }}
            className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-xl p-8 border border-cyan-500/20"
          >
            <h2 className="text-2xl font-semibold text-white mb-6">8. Contact Information and Updates</h2>
            
            <div className="space-y-4 text-slate-300">
              <div>
                <h3 className="text-lg font-medium text-cyan-300 mb-2">Contact Us</h3>
                <p>For questions about these Terms of Service:</p>
                <ul className="space-y-1 ml-4 mt-2">
                  <li>• Email: legal@legalsaathi.com</li>
                  <li>• Support: support@legalsaathi.com</li>
                  <li>• Response time: Within 48 hours</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-cyan-300 mb-2">Terms Updates</h3>
                <p>
                  We may update these Terms periodically. Significant changes will be communicated via:
                </p>
                <ul className="space-y-1 ml-4 mt-2">
                  <li>• Email notification to registered users</li>
                  <li>• In-app notifications</li>
                  <li>• Updated "Last modified" date</li>
                </ul>
              </div>
              
              <div className="mt-6 p-4 bg-slate-800/50 rounded-lg">
                <p className="text-sm text-slate-400">
                  <strong>Governing Law:</strong> These Terms are governed by applicable laws. 
                  Any disputes will be resolved through appropriate legal channels. 
                  Continued use of the service after Terms updates constitutes acceptance of the new Terms.
                </p>
              </div>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
}
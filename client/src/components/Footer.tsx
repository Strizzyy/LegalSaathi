
import { motion } from 'framer-motion';
import { Shield, Heart, Zap } from 'lucide-react';

export function Footer() {
  return (
    <footer className="py-16 bg-slate-950 text-white relative z-10 border-t border-slate-800">
      <div className="container mx-auto px-6">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Logo Section */}
          <div className="md:col-span-2">
            <motion.div 
              className="flex items-center space-x-3 mb-6"
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
            >
              <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">LegalSaathi</div>
                <div className="text-cyan-400">AI Legal Assistant</div>
              </div>
            </motion.div>
            <p className="text-slate-400 text-lg max-w-md mb-6">
              Transforming legal document analysis with cutting-edge AI technology, 
              making complex legal processes simple and accessible for everyone.
            </p>
            
            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 max-w-md">
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <div className="text-2xl font-bold text-cyan-400">10,000+</div>
                <div className="text-sm text-slate-400">Users Protected</div>
              </div>
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <div className="text-2xl font-bold text-green-400">99.9%</div>
                <div className="text-sm text-slate-400">Uptime</div>
              </div>
            </div>
          </div>
          
          {/* Product Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <div className="space-y-3">
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                AI Analysis
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Document Upload
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Risk Assessment
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Compliance Check
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Multi-language Support
              </a>
            </div>
          </div>
          
          {/* Support Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Support</h4>
            <div className="space-y-3">
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Help Center
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Contact Us
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Terms of Service
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                API Documentation
              </a>
            </div>
          </div>
        </div>
        
        {/* Features Highlight */}
        <div className="grid md:grid-cols-3 gap-6 mb-12 py-8 border-t border-b border-slate-800">
          <motion.div 
            className="text-center"
            whileHover={{ y: -5 }}
            transition={{ duration: 0.2 }}
          >
            <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-center mx-auto mb-3">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <h5 className="font-semibold text-white mb-2">Privacy First</h5>
            <p className="text-slate-400 text-sm">
              Your documents are processed securely and never stored permanently
            </p>
          </motion.div>
          
          <motion.div 
            className="text-center"
            whileHover={{ y: -5 }}
            transition={{ duration: 0.2 }}
          >
            <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-lg flex items-center justify-center mx-auto mb-3">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <h5 className="font-semibold text-white mb-2">AI Powered</h5>
            <p className="text-slate-400 text-sm">
              Advanced machine learning models provide accurate legal analysis
            </p>
          </motion.div>
          
          <motion.div 
            className="text-center"
            whileHover={{ y: -5 }}
            transition={{ duration: 0.2 }}
          >
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mx-auto mb-3">
              <Heart className="w-6 h-6 text-white" />
            </div>
            <h5 className="font-semibold text-white mb-2">Community Impact</h5>
            <p className="text-slate-400 text-sm">
              Democratizing legal knowledge and protecting users from unfair terms
            </p>
          </motion.div>
        </div>
        
        {/* Bottom Bar */}
        <div className="flex flex-col md:flex-row justify-between items-center pt-8">
          <div className="text-slate-500 mb-4 md:mb-0 text-center md:text-left">
            <p className="mb-2">© 2024 LegalSaathi. All rights reserved.</p>
            <p className="text-sm">
              <strong>Disclaimer:</strong> This tool provides informational analysis only and does not constitute legal advice. 
              Please consult with a qualified legal professional for specific legal matters.
            </p>
          </div>
          
          <div className="flex flex-col items-center md:items-end space-y-2">
            <div className="flex items-center space-x-6">
              <span className="text-slate-500 text-sm">Made with AI</span>
              <div className="google-cloud-badge">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
                </svg>
                <span>Google Cloud</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
              <span className="text-emerald-400 text-sm">System Online</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
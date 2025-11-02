
import { motion } from 'framer-motion';
import { Shield, Heart, Zap } from 'lucide-react';

interface FooterProps {
  onShowPrivacy?: () => void;
  onShowTerms?: () => void;
}

export function Footer({ onShowPrivacy, onShowTerms }: FooterProps) {
  return (
    <footer className="py-20 bg-slate-950 text-white relative z-10 border-t border-slate-800/30">
      <div className="container mx-auto px-6">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          {/* Clean Logo Section */}
          <div className="md:col-span-2">
            <motion.div 
              className="flex items-center space-x-4 mb-8"
              whileHover={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
            >
              <div className="w-14 h-14 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl flex items-center justify-center">
                <Shield className="w-7 h-7 text-white" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">LegalSaathi</div>
                <div className="text-cyan-400">AI Legal Assistant</div>
              </div>
            </motion.div>
            <p className="text-slate-400 leading-relaxed max-w-lg mb-6">
              AI-powered legal document analysis made simple and accessible.
            </p>
            <div className="flex items-center text-green-400">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-3 animate-pulse"></div>
              <span className="font-medium">AI Services Online</span>
            </div>
          </div>
          
          {/* Product Links */}
          <div>
            <h4 className="text-white font-semibold mb-6">Product</h4>
            <div className="space-y-4">
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
            </div>
          </div>
          
          {/* Support Links */}
          <div>
            <h4 className="text-white font-semibold mb-6">Support</h4>
            <div className="space-y-4">
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Help Center
              </a>
              <a href="#" className="block text-slate-400 hover:text-cyan-400 transition-colors">
                Contact Us
              </a>
              <button 
                onClick={onShowPrivacy}
                className="block text-slate-400 hover:text-cyan-400 transition-colors text-left"
              >
                Privacy Policy
              </button>
              <button 
                onClick={onShowTerms}
                className="block text-slate-400 hover:text-cyan-400 transition-colors text-left"
              >
                Terms of Service
              </button>
            </div>
          </div>
        </div>
        
        {/* Clean Features Highlight */}
        <div className="grid md:grid-cols-3 gap-12 mb-16 py-16 border-t border-slate-800/30">
          <motion.div 
            className="text-center group"
            whileHover={{ y: -4 }}
            transition={{ duration: 0.3 }}
          >
            <div className="w-14 h-14 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h5 className="text-xl font-bold text-white mb-4">Privacy First</h5>
            <p className="text-slate-400 text-sm">
              Secure processing, never stored
            </p>
          </motion.div>
          
          <motion.div 
            className="text-center group"
            whileHover={{ y: -4 }}
            transition={{ duration: 0.3 }}
          >
            <div className="w-14 h-14 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <h5 className="text-xl font-bold text-white mb-4">AI Powered</h5>
            <p className="text-slate-400 text-sm">
              Advanced AI for accurate analysis
            </p>
          </motion.div>
          
          <motion.div 
            className="text-center group"
            whileHover={{ y: -4 }}
            transition={{ duration: 0.3 }}
          >
            <div className="w-14 h-14 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Heart className="w-7 h-7 text-white" />
            </div>
            <h5 className="text-xl font-bold text-white mb-4">Community Impact</h5>
            <p className="text-slate-400 text-sm">
              Protecting thousands of users daily
            </p>
          </motion.div>
        </div>
        
        {/* Clean Bottom Bar */}
        <div className="flex flex-col md:flex-row justify-between items-center pt-8 border-t border-slate-800/30">
          <div className="text-slate-500 mb-4 md:mb-0 text-center md:text-left">
            <p className="mb-2">© 2025 LegalSaathi. All rights reserved.</p>
            <p className="text-xs">
              Informational analysis only, not legal advice.
            </p>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="inline-flex items-center px-4 py-2 bg-slate-800/30 border border-slate-700/50 rounded-full text-slate-400 text-sm">
              <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
              </svg>
              <span>Google Cloud</span>
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
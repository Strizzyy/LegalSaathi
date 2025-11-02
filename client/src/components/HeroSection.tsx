
import { motion } from 'framer-motion';
import { Shield, Globe, Users, ArrowDown, Zap } from 'lucide-react';
import { Robot3DLazy } from './Robot3DLazy';

export function HeroSection() {
  const scrollToUpload = () => {
    const uploadSection = document.getElementById('document-upload');
    if (uploadSection) {
      uploadSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center pt-20 pb-16 overflow-hidden">
      {/* Clean Minimalist Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(34,211,238,0.08),transparent_70%)]"></div>
      </div>

      <div className="container mx-auto px-6 relative z-10">
        <div className="text-center max-w-6xl mx-auto">


          {/* Clean Main Heading */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-16"
          >
            <h1 className="text-6xl md:text-8xl font-bold text-white mb-8 leading-tight tracking-tight">
              Transform{' '}
              <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                Legal Documents
              </span>{' '}
              with AI
            </h1>
            <p className="text-xl md:text-2xl text-slate-400 leading-relaxed max-w-3xl mx-auto font-light">
              Transform complex legal language into clear insights
            </p>
          </motion.div>

          {/* Clean Benefits Row */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mb-16"
          >
            <div className="flex flex-wrap justify-center gap-8 text-slate-300">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                <span className="font-medium">Instant Analysis</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                <span className="font-medium">Risk Assessment</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                <span className="font-medium">Plain Language</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                <span className="font-medium">Privacy First</span>
              </div>
            </div>
          </motion.div>

          {/* Clean CTA Section */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="mb-20"
          >
            <button
              onClick={scrollToUpload}
              className="group inline-flex items-center justify-center px-12 py-5 text-xl font-semibold text-white bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl hover:from-cyan-400 hover:to-blue-400 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/25"
            >
              <Zap className="w-6 h-6 mr-3" />
              <span>Start Free Analysis</span>
              <ArrowDown className="w-6 h-6 ml-3 group-hover:translate-y-1 transition-transform" />
            </button>
            <p className="text-slate-500 text-sm mt-4">
              No signup required • Free forever • Privacy protected
            </p>
          </motion.div>

          {/* Clean Features Grid */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="mb-16"
          >
            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              <div className="group bg-slate-800/20 backdrop-blur-sm rounded-3xl p-8 border border-slate-700/30 hover:border-cyan-500/30 transition-all duration-500">
                <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Shield className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-xl font-bold text-white mb-3">Risk Assessment</h4>
                <p className="text-slate-400 leading-relaxed">
                  Traffic light system with confidence scoring
                </p>
              </div>

              <div className="group bg-slate-800/20 backdrop-blur-sm rounded-3xl p-8 border border-slate-700/30 hover:border-emerald-500/30 transition-all duration-500">
                <div className="w-16 h-16 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Globe className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-xl font-bold text-white mb-3">Universal Support</h4>
                <p className="text-slate-400 leading-relaxed">
                  Contracts, agreements, NDAs, and more
                </p>
              </div>

              <div className="group bg-slate-800/20 backdrop-blur-sm rounded-3xl p-8 border border-slate-700/30 hover:border-purple-500/30 transition-all duration-500">
                <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-xl font-bold text-white mb-3">Proven Impact</h4>
                <p className="text-slate-400 leading-relaxed">
                  Protecting thousands of users daily
                </p>
              </div>
            </div>
          </motion.div>

          {/* Robot positioned outside main content flow */}
          <Robot3DLazy />

          {/* Clean Google Cloud Badge */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 1.0 }}
            className="flex justify-center"
          >
            <div className="inline-flex items-center px-6 py-3 bg-slate-800/30 backdrop-blur-sm border border-slate-700/50 rounded-full text-slate-400 font-medium">
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
              </svg>
              <span>Powered by Google Cloud AI</span>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Minimal Floating Elements */}
      <div className="absolute top-1/4 left-10 w-32 h-32 bg-cyan-500/5 rounded-full blur-3xl animate-float"></div>
      <div className="absolute bottom-1/4 right-10 w-40 h-40 bg-blue-500/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
    </section>
  );
}
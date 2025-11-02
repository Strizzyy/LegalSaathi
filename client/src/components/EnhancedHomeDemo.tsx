import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, CheckCircle, Zap } from 'lucide-react';

export function EnhancedHomeDemo() {
  return (
    <section className="py-20 bg-gradient-to-b from-slate-900 to-slate-950 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 hero-background-enhanced"></div>
      
      <div className="container mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 rounded-full text-cyan-400 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4 mr-2" />
            Enhanced UI/UX Experience
          </div>
          
          <h2 className="text-4xl md:text-6xl font-bold text-white mb-8">
            Improved{' '}
            <span className="text-gradient-enhanced">
              User Experience
            </span>
          </h2>
          
          <p className="text-xl md:text-2xl text-slate-300 max-w-4xl mx-auto leading-relaxed mb-12">
            Experience our enhanced interface with better visual hierarchy, improved animations, 
            and more intuitive user interactions.
          </p>

          {/* Key Improvements */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {[
              {
                icon: Sparkles,
                title: 'Enhanced Visuals',
                description: 'Better gradients, animations, and visual hierarchy'
              },
              {
                icon: Zap,
                title: 'Improved Performance',
                description: 'Optimized animations and smoother interactions'
              },
              {
                icon: CheckCircle,
                title: 'Better UX',
                description: 'More intuitive navigation and clearer CTAs'
              },
              {
                icon: ArrowRight,
                title: 'Modern Design',
                description: 'Contemporary UI patterns and micro-interactions'
              }
            ].map((item, index) => {
              const IconComponent = item.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="feature-card-enhanced glass-morphism rounded-2xl p-6"
                >
                  <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center mb-4 mx-auto">
                    <IconComponent className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-slate-400 text-sm">{item.description}</p>
                </motion.div>
              );
            })}
          </div>

          {/* Enhanced CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            viewport={{ once: true }}
          >
            <button className="btn-primary-enhanced px-8 py-4 rounded-2xl text-white font-semibold text-lg inline-flex items-center focus-ring-enhanced">
              <Sparkles className="w-5 h-5 mr-2" />
              Experience the Enhancement
              <ArrowRight className="w-5 h-5 ml-2" />
            </button>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
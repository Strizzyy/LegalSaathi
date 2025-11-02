import { motion } from 'framer-motion';
import { FileText, Shield, Search, Images, ArrowRight, Sparkles, Clock, Target } from 'lucide-react';

interface ProductSectionProps {
  onNavigateToDocumentSummary: () => void;
  onNavigateToRiskAssessment: () => void;
  onNavigateToClauseAnalysis: () => void;
  onNavigateToMultipleImages: () => void;
}

export function ProductSection({ 
  onNavigateToDocumentSummary, 
  onNavigateToRiskAssessment, 
  onNavigateToClauseAnalysis,
  onNavigateToMultipleImages
}: ProductSectionProps) {
  const products = [
    {
      id: 'document-summary',
      title: 'Document Summary',
      description: 'AI-powered summaries with key insights.',
      icon: FileText,
      color: 'from-cyan-500 to-blue-500',
      onClick: onNavigateToDocumentSummary
    },
    {
      id: 'risk-assessment',
      title: 'Risk Assessment',
      description: 'Traffic light risk analysis with confidence scoring.',
      icon: Shield,
      color: 'from-emerald-500 to-cyan-500',
      onClick: onNavigateToRiskAssessment
    },
    {
      id: 'clause-analysis',
      title: 'Clause Analysis',
      description: 'Detailed clause explanations and legal implications.',
      icon: Search,
      color: 'from-purple-500 to-pink-500',
      onClick: onNavigateToClauseAnalysis
    },
    {
      id: 'multiple-images',
      title: 'Multiple Image Analysis',
      description: 'OCR analysis of multiple document images.',
      icon: Images,
      color: 'from-orange-500 to-red-500',
      onClick: onNavigateToMultipleImages
    }
  ];

  return (
    <section className="py-24 bg-slate-900 relative">
      <div className="container mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Our{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Products
            </span>
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            AI-powered legal analysis tools for every need.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {products.map((product, index) => {
            const IconComponent = product.icon;
            return (
              <motion.div
                key={product.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="group"
              >
                <div className="bg-slate-800/30 backdrop-blur-sm rounded-3xl p-8 border border-slate-700/50 hover:border-cyan-500/50 transition-all duration-500 h-full flex flex-col hover:transform hover:scale-105">
                  <div className={`w-16 h-16 bg-gradient-to-r ${product.color} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <IconComponent className="w-8 h-8 text-white" />
                  </div>
                  
                  <h3 className="text-2xl font-bold text-white mb-4">{product.title}</h3>
                  <p className="text-slate-400 text-lg leading-relaxed mb-8 flex-grow">
                    {product.description}
                  </p>
                  
                  <button
                    onClick={product.onClick}
                    className={`group/btn inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r ${product.color} text-white rounded-2xl hover:shadow-xl hover:shadow-cyan-500/25 transition-all duration-300 transform hover:scale-105 font-semibold`}
                  >
                    <span className="mr-2">Explore</span>
                    <ArrowRight className="w-5 h-5 group-hover/btn:translate-x-1 transition-transform" />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
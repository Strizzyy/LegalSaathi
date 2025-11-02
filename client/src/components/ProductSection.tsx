import { motion } from 'framer-motion';
import { FileText, Shield, Search, Images, ArrowRight } from 'lucide-react';

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
      description: 'Get comprehensive AI-powered summaries of your legal documents with key insights and recommendations.',
      icon: FileText,
      color: 'from-cyan-500 to-blue-500',
      onClick: onNavigateToDocumentSummary
    },
    {
      id: 'risk-assessment',
      title: 'Risk Assessment',
      description: 'Analyze potential risks in your documents with our traffic light system and confidence scoring.',
      icon: Shield,
      color: 'from-emerald-500 to-cyan-500',
      onClick: onNavigateToRiskAssessment
    },
    {
      id: 'clause-analysis',
      title: 'Clause Analysis',
      description: 'Deep dive into individual clauses with detailed explanations and legal implications.',
      icon: Search,
      color: 'from-purple-500 to-pink-500',
      onClick: onNavigateToClauseAnalysis
    },
    {
      id: 'multiple-images',
      title: 'Multiple Image Analysis',
      description: 'Upload multiple images of legal documents to analyze them as a single comprehensive document using OCR.',
      icon: Images,
      color: 'from-orange-500 to-red-500',
      onClick: onNavigateToMultipleImages
    }
  ];

  return (
    <section className="py-20 bg-slate-900 relative">
      <div className="container mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Our <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">Products</span>
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Explore our comprehensive suite of AI-powered legal analysis tools designed to make complex legal documents accessible and understandable.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {products.map((product, index) => {
            const IconComponent = product.icon;
            return (
              <motion.div
                key={product.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2 }}
                className="group"
              >
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 hover:border-cyan-500/50 transition-all duration-300 h-full flex flex-col">
                  <div className={`w-16 h-16 bg-gradient-to-r ${product.color} rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                    <IconComponent className="w-8 h-8 text-white" />
                  </div>
                  
                  <h3 className="text-2xl font-bold text-white mb-4">{product.title}</h3>
                  <p className="text-slate-400 text-lg leading-relaxed mb-8 flex-grow">
                    {product.description}
                  </p>
                  
                  <button
                    onClick={product.onClick}
                    className={`group/btn inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r ${product.color} text-white rounded-xl hover:shadow-lg hover:shadow-cyan-500/25 transition-all duration-300 transform hover:scale-105 font-semibold`}
                  >
                    <span className="mr-2">Explore {product.title}</span>
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
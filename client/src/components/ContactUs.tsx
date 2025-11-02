import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Mail, Linkedin, Phone, Github, ArrowLeft, Send, MapPin, Clock } from 'lucide-react';
import { Button } from './ui/button';

interface ContactUsProps {
  onClose: () => void;
}

interface TeamMember {
  name: string;
  role: string;
  email: string;
  linkedin: string;
  phone: string;
  github: string;
}

interface ContactForm {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export function ContactUs({ onClose }: ContactUsProps) {
  const [formData, setFormData] = useState<ContactForm>({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  // Track scroll position to show/hide floating back button
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      setIsScrolled(scrollTop > 200); // Show floating button after scrolling 200px
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const teamMembers: TeamMember[] = [
    {
      name: "Rohan Singh",
      role: "Lead Developer & Project Manager",
      email: "rohan.singh@legalsaathi.com",
      linkedin: "https://linkedin.com/in/rohan-singh",
      phone: "+91-XXXX-XXXX-XX",
      github: "https://github.com/rohan-singh"
    },
    {
      name: "Shubh Sharma",
      role: "AI/ML Engineer",
      email: "shubh.sharma@legalsaathi.com",
      linkedin: "https://linkedin.com/in/shubh-sharma",
      phone: "+91-XXXX-XXXX-XX",
      github: "https://github.com/shubh-sharma"
    },
    {
      name: "Swez Bhardwaj",
      role: "Frontend Developer & UX Designer",
      email: "swez.bhardwaj@legalsaathi.com",
      linkedin: "https://linkedin.com/in/swez-bhardwaj",
      phone: "+91-XXXX-XXXX-XX",
      github: "https://github.com/swez-bhardwaj"
    },
    {
      name: "Harsh Mishra",
      role: "Backend Developer & DevOps Engineer",
      email: "harsh.mishra@legalsaathi.com",
      linkedin: "https://linkedin.com/in/harsh-mishra",
      phone: "+91-XXXX-XXXX-XX",
      github: "https://github.com/harsh-mishra"
    }
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Simulate form submission
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Reset form
    setFormData({
      name: '',
      email: '',
      subject: '',
      message: ''
    });
    setIsSubmitting(false);
    
    // Show success message (you can integrate with notification service)
    alert('Thank you for your message! We\'ll get back to you soon.');
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 pt-20 relative">
      {/* Floating Back Button */}
      <motion.button
        onClick={onClose}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ 
          opacity: isScrolled ? 1 : 0, 
          scale: isScrolled ? 1 : 0.8,
          y: isScrolled ? 0 : 20
        }}
        transition={{ duration: 0.3 }}
        className={`fixed top-24 left-6 z-50 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white p-3 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 group ${
          isScrolled ? 'pointer-events-auto' : 'pointer-events-none'
        }`}
        style={{ backdropFilter: 'blur(10px)' }}
      >
        <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
        <span className="sr-only">Back to Home</span>
      </motion.button>

      <div className="container mx-auto px-6 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          {/* Static Back Button - visible at top */}
          <motion.button
            onClick={onClose}
            initial={{ opacity: 1 }}
            animate={{ opacity: isScrolled ? 0.5 : 1 }}
            transition={{ duration: 0.3 }}
            className="inline-flex items-center space-x-2 text-cyan-400 hover:text-cyan-300 transition-colors mb-8 group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span>Back to Home</span>
          </motion.button>
          
          <h1 className="text-5xl font-bold text-white mb-6">
            Get in <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Touch</span>
          </h1>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Have questions about LegalSaathi? Need support? Want to collaborate? 
            We'd love to hear from you. Reach out to us through any of the channels below.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Contact Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl p-8 border border-slate-700"
          >
            <h2 className="text-3xl font-bold text-white mb-6">Send us a Message</h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
                    placeholder="Your full name"
                  />
                </div>
                
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
                    placeholder="your.email@example.com"
                  />
                </div>
              </div>
              
              <div>
                <label htmlFor="subject" className="block text-sm font-medium text-slate-300 mb-2">
                  Subject
                </label>
                <input
                  type="text"
                  id="subject"
                  name="subject"
                  value={formData.subject}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
                  placeholder="What's this about?"
                />
              </div>
              
              <div>
                <label htmlFor="message" className="block text-sm font-medium text-slate-300 mb-2">
                  Message
                </label>
                <textarea
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleInputChange}
                  required
                  rows={6}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all resize-none"
                  placeholder="Tell us more about your inquiry..."
                />
              </div>
              
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-medium py-3 px-6 rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Sending...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-2">
                    <Send className="w-4 h-4" />
                    <span>Send Message</span>
                  </div>
                )}
              </Button>
            </form>
          </motion.div>

          {/* Contact Information */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            {/* General Contact Info */}
            <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl p-8 border border-slate-700">
              <h3 className="text-2xl font-bold text-white mb-6">Contact Information</h3>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                    <Mail className="w-6 h-6 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-slate-300 text-sm">General Inquiries</p>
                    <p className="text-white font-medium">contact@legalsaathi.com</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                    <Phone className="w-6 h-6 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-slate-300 text-sm">Support Hotline</p>
                    <p className="text-white font-medium">+91-XXXX-XXXX-XX</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                    <MapPin className="w-6 h-6 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-slate-300 text-sm">Location</p>
                    <p className="text-white font-medium">India</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                    <Clock className="w-6 h-6 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-slate-300 text-sm">Response Time</p>
                    <p className="text-white font-medium">Within 24 hours</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Team Members Contact */}
            <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl p-8 border border-slate-700">
              <h3 className="text-2xl font-bold text-white mb-6">Team Members</h3>
              
              <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="space-y-4"
              >
                {teamMembers.map((member) => (
                  <motion.div
                    key={member.name}
                    variants={itemVariants}
                    className="p-4 bg-slate-700/30 rounded-lg border border-slate-600/50 hover:border-cyan-500/50 transition-all duration-300"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-white">{member.name}</h4>
                        <p className="text-sm text-cyan-400">{member.role}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <a
                        href={`mailto:${member.email}`}
                        className="p-2 bg-slate-600/50 rounded-lg hover:bg-slate-500/50 transition-colors group"
                        title="Email"
                      >
                        <Mail className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                      </a>
                      
                      <a
                        href={member.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 bg-slate-600/50 rounded-lg hover:bg-slate-500/50 transition-colors group"
                        title="LinkedIn"
                      >
                        <Linkedin className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                      </a>
                      
                      <a
                        href={`tel:${member.phone}`}
                        className="p-2 bg-slate-600/50 rounded-lg hover:bg-slate-500/50 transition-colors group"
                        title="Phone"
                      >
                        <Phone className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                      </a>
                      
                      <a
                        href={member.github}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 bg-slate-600/50 rounded-lg hover:bg-slate-500/50 transition-colors group"
                        title="GitHub"
                      >
                        <Github className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                      </a>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </div>

            {/* FAQ Section */}
            <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl p-8 border border-slate-700">
              <h3 className="text-2xl font-bold text-white mb-6">Quick Questions?</h3>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-white mb-2">How secure is my data?</h4>
                  <p className="text-slate-300 text-sm">We use enterprise-grade encryption and never store your documents permanently.</p>
                </div>
                
                <div>
                  <h4 className="font-medium text-white mb-2">What file formats do you support?</h4>
                  <p className="text-slate-300 text-sm">PDF, DOC, DOCX, and TXT files up to 10MB in size.</p>
                </div>
                
                <div>
                  <h4 className="font-medium text-white mb-2">Is LegalSaathi free to use?</h4>
                  <p className="text-slate-300 text-sm">Yes! Our core features are completely free for all users.</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default ContactUs;
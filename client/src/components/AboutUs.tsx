import { motion } from 'framer-motion';
import { Mail, Linkedin, Phone, Github, ArrowLeft } from 'lucide-react';

interface TeamMember {
  name: string;
  role: string;
  email: string;
  linkedin: string;
  phone: string;
  github: string;
  bio: string;
  avatar?: string;
}

interface AboutUsProps {
  onClose: () => void;
}

export function AboutUs({ onClose }: AboutUsProps) {
  const teamMembers: TeamMember[] = [
    {
      name: "Rohan Singh",
      role: "Lead Developer & Project Manager",
      email: "rohan.singh@legalsaathi.com",
      linkedin: "https://linkedin.com/in/rohan-singh",
      phone: "+91-XXXX-XXXX-XX",
      github: "https://github.com/rohan-singh",
      bio: "Passionate about leveraging AI to make legal services accessible to everyone. Experienced in full-stack development and project management.",
      avatar: "/api/placeholder/150/150"
    },
    {
      name: "Shubh Sharma",
      role: "AI/ML Engineer",
      email: "shubh.sharma@legalsaathi.com",
      linkedin: "https://linkedin.com/in/shubh-sharma",
      phone: "+91-XXXX-XXXX-XX",
      github: "https://github.com/shubh-sharma",
      bio: "Specializes in natural language processing and machine learning algorithms for legal document analysis and risk assessment.",
      avatar: "/api/placeholder/150/150"
    },
    {
      name: "Swez Bhardwaj",
      role: "Frontend Developer & UX Designer",
      email: "swez.bhardwaj@legalsaathi.com",
      linkedin: "https://linkedin.com/in/swez-bhardwaj",
      phone: "+91-XXXX-XXXX-XX",
      github: "https://github.com/swez-bhardwaj",
      bio: "Creates intuitive user experiences and responsive interfaces. Focuses on accessibility and user-centered design principles.",
      avatar: "/api/placeholder/150/150"
    },
    {
      name: "Harsh Mishra",
      role: "Backend Developer & DevOps Engineer",
      email: "harsh.mishra@legalsaathi.com",
      linkedin: "https://linkedin.com/in/harsh-mishra",
      phone: "+91-XXXX-XXXX-XX",
      github: "https://github.com/harsh-mishra",
      bio: "Builds scalable backend systems and manages cloud infrastructure. Ensures security and performance optimization.",
      avatar: "/api/placeholder/150/150"
    }
  ];

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
    <div className="min-h-screen bg-slate-900 pt-20">
      <div className="container mx-auto px-6 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <button
            onClick={onClose}
            className="inline-flex items-center space-x-2 text-cyan-400 hover:text-cyan-300 transition-colors mb-8 group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            <span>Back to Home</span>
          </button>
          
          <h1 className="text-5xl font-bold text-white mb-6">
            Meet Our <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Team</span>
          </h1>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            We are a passionate team of developers, designers, and AI enthusiasts dedicated to making legal services 
            accessible and understandable for everyone through innovative technology.
          </p>
        </motion.div>

        {/* Mission Statement */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded-2xl p-8 mb-16 border border-slate-600"
        >
          <h2 className="text-3xl font-bold text-white mb-4">Our Mission</h2>
          <p className="text-lg text-slate-300 leading-relaxed">
            LegalSaathi aims to democratize legal knowledge by providing AI-powered document analysis, 
            risk assessment, and legal insights. We believe that everyone deserves access to clear, 
            understandable legal guidance, regardless of their background or resources.
          </p>
        </motion.div>

        {/* Team Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8 mb-16"
        >
          {teamMembers.map((member) => (
            <motion.div
              key={member.name}
              variants={itemVariants}
              className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl p-8 border border-slate-700 hover:border-cyan-500/50 transition-all duration-300 group hover:shadow-xl hover:shadow-cyan-500/10"
            >
              {/* Avatar */}
              <div className="flex flex-col items-center mb-6">
                <div className="w-32 h-32 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 p-1 mb-4 group-hover:scale-105 transition-transform duration-300">
                  <div className="w-full h-full rounded-full bg-slate-800 flex items-center justify-center">
                    <span className="text-3xl font-bold text-white">
                      {member.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">{member.name}</h3>
                <p className="text-cyan-400 font-medium text-lg">{member.role}</p>
              </div>

              {/* Bio */}
              <p className="text-slate-300 text-center mb-6 leading-relaxed">
                {member.bio}
              </p>

              {/* Contact Links */}
              <div className="grid grid-cols-2 gap-4">
                <a
                  href={`mailto:${member.email}`}
                  className="flex items-center space-x-2 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-600/50 transition-colors group/link"
                >
                  <Mail className="w-4 h-4 text-cyan-400 group-hover/link:scale-110 transition-transform" />
                  <span className="text-sm text-slate-300 group-hover/link:text-white transition-colors">Email</span>
                </a>
                
                <a
                  href={member.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-600/50 transition-colors group/link"
                >
                  <Linkedin className="w-4 h-4 text-cyan-400 group-hover/link:scale-110 transition-transform" />
                  <span className="text-sm text-slate-300 group-hover/link:text-white transition-colors">LinkedIn</span>
                </a>
                
                <a
                  href={`tel:${member.phone}`}
                  className="flex items-center space-x-2 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-600/50 transition-colors group/link"
                >
                  <Phone className="w-4 h-4 text-cyan-400 group-hover/link:scale-110 transition-transform" />
                  <span className="text-sm text-slate-300 group-hover/link:text-white transition-colors">Phone</span>
                </a>
                
                <a
                  href={member.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-600/50 transition-colors group/link"
                >
                  <Github className="w-4 h-4 text-cyan-400 group-hover/link:scale-110 transition-transform" />
                  <span className="text-sm text-slate-300 group-hover/link:text-white transition-colors">GitHub</span>
                </a>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Technology Stack */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded-2xl p-8 border border-slate-600"
        >
          <h2 className="text-3xl font-bold text-white mb-6 text-center">Our Technology Stack</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { name: "React", category: "Frontend" },
              { name: "TypeScript", category: "Language" },
              { name: "Python", category: "Backend" },
              { name: "FastAPI", category: "API Framework" },
              { name: "Google Cloud AI", category: "AI/ML" },
              { name: "Firebase", category: "Authentication" },
              { name: "Tailwind CSS", category: "Styling" },
              { name: "Framer Motion", category: "Animations" }
            ].map((tech) => (
              <div
                key={tech.name}
                className="text-center p-4 bg-slate-700/30 rounded-lg border border-slate-600/50"
              >
                <h4 className="font-semibold text-white mb-1">{tech.name}</h4>
                <p className="text-sm text-cyan-400">{tech.category}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
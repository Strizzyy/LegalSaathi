import { motion } from 'framer-motion';
import './Robot3D.css';

export const Robot3D = () => {
  return (
    <motion.div
      className="robot-container"
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, type: "spring" }}
    >
      <div className="speech-bubble">Hello, explorer. Team Lunatics is online.</div>
      <div className="robot">
        <div className="head">
          <div className="antenna"></div>
          <div className="ear left"></div>
          <div className="ear right"></div>
          <div className="screen">
            <div className="eyes">
              <div className="eye left"></div>
              <div className="eye right"></div>
            </div>
            <div className="smile"></div>
          </div>
        </div>
        <div className="body">
          <div className="arm left">
            <div className="hand"></div>
          </div>
          <div className="arm right">
            <div className="hand"></div>
          </div>
          <div className="legs">
            <div className="leg">
              <div className="foot"></div>
            </div>
            <div className="leg">
              <div className="foot"></div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
import { Brain, ArrowRight, Eye, Users } from 'lucide-react';
import { Modal } from './Modal';

interface ExpertDashboardPopupProps {
  isVisible: boolean;
  onGoToDashboard: () => void;
  onStayHere: () => void;
  onClose: () => void;
}

export function ExpertDashboardPopup({
  isVisible,
  onGoToDashboard,
  onStayHere,
  onClose
}: ExpertDashboardPopupProps) {
  return (
    <Modal
      isOpen={isVisible}
      onClose={onClose}
      title="Expert Review Submitted"
      maxWidth="lg"
    >
      <div className="space-y-6">
        {/* Success Message */}
        <div className="flex items-start space-x-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
          <Brain className="w-6 h-6 text-emerald-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-2">
              Request Successfully Submitted!
            </h3>
            <p className="text-slate-300">
              Your document has been queued for expert review. In a production environment, 
              you would receive detailed analysis results via email within 24-48 hours.
            </p>
          </div>
        </div>

        {/* Demo Explanation */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <Eye className="w-5 h-5 text-blue-400 mr-2" />
            <h4 className="font-semibold text-white">Demo Mode</h4>
          </div>
          <p className="text-slate-300 text-sm mb-3">
            Since this is a demonstration, would you like to see how the expert dashboard 
            looks where legal professionals would manage and review low-confidence documents? 
            It will open in a new tab so you can keep your analysis results.
          </p>
          <div className="bg-slate-700/50 rounded-lg p-3 mt-3">
            <h5 className="text-sm font-medium text-white mb-2">You'll see:</h5>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>• Expert review queue management interface</li>
              <li>• Your submitted request with detailed analysis</li>
              <li>• How experts would prioritize and assign reviews</li>
              <li>• Professional workflow for human-in-the-loop system</li>
            </ul>
          </div>
        </div>

        {/* Request Summary */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="font-semibold text-white mb-3 flex items-center">
            <Users className="w-4 h-4 mr-2 text-blue-400" />
            Your Review Request
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-slate-400">Request ID</p>
              <p className="text-white font-medium">demo-hitl-001</p>
            </div>
            <div>
              <p className="text-slate-400">Priority</p>
              <p className="text-orange-400 font-medium">High</p>
            </div>
            <div>
              <p className="text-slate-400">AI Confidence</p>
              <p className="text-red-400 font-medium">35%</p>
            </div>
            <div>
              <p className="text-slate-400">Estimated Time</p>
              <p className="text-white font-medium">24 hours</p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3 pt-4">
          <button
            onClick={onGoToDashboard}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center shadow-lg hover:shadow-xl"
          >
            <Brain className="w-4 h-4 mr-2" />
            Open Expert Dashboard
            <ArrowRight className="w-4 h-4 ml-2" />
          </button>
          <button
            onClick={onStayHere}
            className="flex-1 bg-slate-600 hover:bg-slate-700 text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            Stay Here
          </button>
        </div>

        {/* Footer Note */}
        <div className="text-center text-sm text-slate-400 pt-2 border-t border-slate-700">
          <p>This is a demonstration of the human-in-the-loop expert review system</p>
        </div>
      </div>
    </Modal>
  );
}
import { lazy, Suspense } from 'react';
import './Robot3D.css';

// Lazy load the Robot3D component
const Robot3DComponent = lazy(() => 
  import('./Robot3D').then(module => ({ default: module.Robot3D }))
);

// Loading fallback component
const Robot3DLoading = () => (
  <div className="robot-container robot-loading">
    <div className="robot-placeholder">
      <div className="loading-spinner"></div>
    </div>
  </div>
);

// Note: Error boundary fallback is handled within the Robot3D component itself

export const Robot3DLazy = () => {
  return (
    <Suspense fallback={<Robot3DLoading />}>
      <Robot3DComponent />
    </Suspense>
  );
};
/**
 * Expert Router Component
 * Handles routing for expert portal pages
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ExpertLogin from '../pages/ExpertLogin';
import ExpertDashboard from '../pages/ExpertDashboard';
import DocumentReviewInterface from './DocumentReviewInterface';

export const ExpertRouter: React.FC = () => {
  return (
    <Routes>
      <Route path="/expert-portal" element={<ExpertLogin />} />
      <Route path="/expert-dashboard" element={<ExpertDashboard />} />
      <Route path="/expert-review/:reviewId" element={<DocumentReviewInterface />} />
      <Route path="/expert/*" element={<Navigate to="/expert-portal" replace />} />
    </Routes>
  );
};
/**
 * Admin Access Button - Shows only for admin users
 * Provides access to the cost monitoring dashboard
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { adminCostService } from '../../services/adminCostService';

const AdminAccessButton: React.FC = () => {
    const { user } = useAuth();
    const [isAdmin, setIsAdmin] = useState<boolean>(false);

    const [checking, setChecking] = useState<boolean>(false);

    useEffect(() => {
        const checkAdminAccess = async () => {
            if (!user) {
                setIsAdmin(false);
                return;
            }

            setChecking(true);
            try {
                const hasAccess = await adminCostService.checkAdminAccess();
                setIsAdmin(hasAccess);
            } catch (error) {
                setIsAdmin(false);
            } finally {
                setChecking(false);
            }
        };

        checkAdminAccess();
    }, [user]);

    // Don't render anything if user is not admin
    if (!user || !isAdmin || checking) {
        return null;
    }

    const handleAdminClick = () => {
        // Navigate to admin page
        window.history.pushState({}, '', '/admin');
        window.dispatchEvent(new PopStateEvent('popstate'));
    };

    return (
        <button
            onClick={handleAdminClick}
            className="flex items-center space-x-2 px-3 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            title="Admin Cost Monitoring Dashboard"
        >
            <span>🔒</span>
            <span>Admin</span>
        </button>
    );
};

export default AdminAccessButton;
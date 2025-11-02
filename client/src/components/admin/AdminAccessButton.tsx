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
                console.log('Admin button: No user authenticated');
                setIsAdmin(false);
                return;
            }

            console.log('Admin button: Checking access for user:', user.email);
            setChecking(true);
            try {
                const hasAccess = await adminCostService.checkAdminAccess();
                console.log('Admin button: Access check result:', hasAccess);
                setIsAdmin(hasAccess);
            } catch (error) {
                console.error('Admin button: Access check error:', error);
                setIsAdmin(false);
            } finally {
                setChecking(false);
            }
        };

        checkAdminAccess();
    }, [user]);

    // Don't render anything if user is not admin or still checking
    if (!user || checking) {
        return null;
    }

    // In development mode, show admin button for admin emails even if server check fails
    const adminEmails = ['23cd3034@rgipt.ac.in', 'admin@legalsaathi.com', 'k.sharmashubh123@gmail.com', '23mc3055@rgipt.ac.in'];
    const isAdminEmail = adminEmails.includes(user.email || '');
    
    if (!isAdmin && !isAdminEmail) {
        return null;
    }

    const handleAdminClick = () => {
        // Navigate to admin page
        window.history.pushState({}, '', '/admin');
        window.dispatchEvent(new PopStateEvent('popstate'));
    };

    const buttonClass = isAdmin 
        ? "flex items-center space-x-2 px-3 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        : "flex items-center space-x-2 px-3 py-2 text-sm bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors";
    
    const buttonTitle = isAdmin 
        ? "Admin Cost Monitoring Dashboard"
        : "Admin Dashboard (Development Mode)";

    return (
        <button
            onClick={handleAdminClick}
            className={buttonClass}
            title={buttonTitle}
        >
            <span>Admin</span>
            {!isAdmin && isAdminEmail && <span className="text-xs">*</span>}
        </button>
    );
};

export default AdminAccessButton;
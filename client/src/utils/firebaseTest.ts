/**
 * Simple Firebase connection test utility
 */

import { auth } from '../firebaseConfig';
import { connectAuthEmulator } from 'firebase/auth';

export const testFirebaseConnection = (): boolean => {
    try {
        // Check if Firebase auth is properly initialized
        if (!auth) {
            console.error('Firebase auth is not initialized');
            return false;
        }

        // Check if environment variables are loaded
        const config = {
            apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
            authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
            projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
        };

        if (!config.apiKey || !config.authDomain || !config.projectId) {
            console.error('Firebase environment variables are not properly configured');
            console.log('Current config:', config);
            return false;
        }

        console.log('Firebase configuration test passed');
        console.log('Project ID:', config.projectId);
        console.log('Auth Domain:', config.authDomain);
        return true;
    } catch (error) {
        console.error('Firebase configuration test failed:', error);
        return false;
    }
};

// For development: connect to Firebase Auth emulator if running locally
export const connectToEmulatorIfNeeded = () => {
    if (import.meta.env.DEV) {
        try {
            // Only connect to emulator if not already connected
            connectAuthEmulator(auth, 'http://localhost:9099');
            console.log('Connected to Firebase Auth emulator');
        } catch (error) {
            // Emulator connection might fail if already connected or not available
            console.log('Firebase Auth emulator not available or already connected, using production');
        }
    }
};
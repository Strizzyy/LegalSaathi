/**
 * Firebase configuration for client-side authentication
 */

// Import the functions you need from the SDKs you need
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDcBcTHtRAwRafi49t1Zob8up6vJ3sjles",
  authDomain: "legal-saathi-209a4.firebaseapp.com",
  projectId: "legal-saathi-209a4",
  storageBucket: "legal-saathi-209a4.firebasestorage.app",
  messagingSenderId: "147226221819",
  appId: "1:147226221819:web:ae31d2fa8d98a747e5645e"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

export default app;  
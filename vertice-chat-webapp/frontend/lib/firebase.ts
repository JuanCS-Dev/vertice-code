import { initializeApp, getApps } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Firebase config - with fallback for build time
const firebaseConfig = {
  apiKey: "AQ.Ab8RN6KEdIApACMC2Ozz95OJTOZyAWe6AZhMhTbD0qSD7CG_hA",
  authDomain: "vertice-ai.firebaseapp.com",
  projectId: "vertice-ai",
  storageBucket: "vertice-ai.firebasestorage.app",
  messagingSenderId: "239800439060",
  appId: "1:239800439060:web:4f6c41b817c16260a7f201",
};

// Initialize Firebase (Singleton pattern)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

export const auth = getAuth(app);
export const db = getFirestore(app);

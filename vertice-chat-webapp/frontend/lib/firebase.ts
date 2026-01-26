import { initializeApp, getApps } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const requiredEnv = (name: string): string => {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
};

// Firebase client config (do not hardcode credentials/keys)
const firebaseConfig = {
  apiKey: requiredEnv('NEXT_PUBLIC_FIREBASE_API_KEY'),
  authDomain: requiredEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN'),
  projectId: requiredEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID'),
  storageBucket: requiredEnv('NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET'),
  messagingSenderId: requiredEnv('NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID'),
  appId: requiredEnv('NEXT_PUBLIC_FIREBASE_APP_ID'),
};

// Initialize Firebase (Singleton pattern)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

export const auth = getAuth(app);
export const db = getFirestore(app);

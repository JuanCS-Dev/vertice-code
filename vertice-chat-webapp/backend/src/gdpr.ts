import express from 'express';
import { Firestore } from '@google-cloud/firestore';
import { VertexAI } from '@google-cloud/vertexai';
import { logAudit, requireAuth } from './security';

const firestore = new Firestore({ projectId: 'vertice-ai' });
const vertexAI = new VertexAI({ project: 'vertice-ai' });

// GDPR Data Subject Rights Implementation

// Article 15: Right of access
export async function handleDataAccess(userId: string): Promise<any> {
  logAudit('data_access_request', userId, { article: 15 });

  try {
    // Collect data from all sources
    const userDoc = await firestore.collection('users').doc(userId).get();
    const chatHistory = await firestore.collection('chats')
      .where('userId', '==', userId)
      .orderBy('timestamp', 'desc')
      .limit(100)
      .get();

    const usageData = await firestore.collection('usage')
      .where('userId', '==', userId)
      .orderBy('timestamp', 'desc')
      .limit(30)
      .get();

    // Structure response according to GDPR Article 15
    const dataPackage = {
      personalData: {
        profile: userDoc.data(),
        dataCollected: new Date(userDoc.data()?.createdAt),
        purposes: [
          'AI-powered code assistance',
          'Account management',
          'Usage analytics'
        ],
        legalBasis: 'Contract (Terms of Service)',
        retentionPeriod: 'Account active + 3 years'
      },
      chatHistory: chatHistory.docs.map(doc => ({
        id: doc.id,
        timestamp: doc.data().timestamp,
        messages: doc.data().messages,
    // Generate content (simplified for now, will add streaming later)
    const logData = {
      timestamp: new Date().toISOString(),
      action: 'ai_processing',
      aiModel: doc.data().model || 'gemini-2.5-pro'
    };
      })),
      usageAnalytics: usageData.docs.map(doc => ({
        date: doc.data().timestamp,
        tokensUsed: doc.data().tokensUsed,
        featuresAccessed: doc.data().features,
        ipAddress: 'anonymized' // Never reveal actual IP
      })),
      dataRecipients: [
        { name: 'Google Cloud (Firestore)', purpose: 'Database storage', location: 'Multi-region' },
        { name: 'Google Vertex AI', purpose: 'AI processing', location: 'US' },
        { name: 'Stripe', purpose: 'Payment processing', location: 'US' }
      ],
      exportFormat: 'JSON',
      exportDate: new Date().toISOString()
    };

    return dataPackage;
  } catch (error) {
    logAudit('data_access_error', userId, { error: (error as Error).message });
    throw new Error('Failed to retrieve user data');
  }
}

// Article 16: Right to rectification
export async function handleDataRectification(userId: string, corrections: any): Promise<void> {
  logAudit('data_rectification_request', userId, { article: 16, corrections });

  try {
    const userRef = firestore.collection('users').doc(userId);

    // Validate corrections (only allow certain fields)
    const allowedFields = ['name', 'preferences'];
    const validatedCorrections: Record<string, any> = {};

    for (const [field, value] of Object.entries(corrections)) {
      if (allowedFields.includes(field)) {
        validatedCorrections[field] = value;
      }
    }

    await userRef.update({
      ...validatedCorrections,
      rectifiedAt: new Date(),
      rectificationReason: 'User request under GDPR Article 16'
    });

    logAudit('data_rectification_completed', userId, { correctedFields: Object.keys(validatedCorrections) });
  } catch (error) {
    logAudit('data_rectification_error', userId, { error: (error as Error).message });
    throw new Error('Failed to rectify user data');
  }
}

// Article 17: Right to erasure (Right to be forgotten)
export async function handleDataErasure(userId: string, reason: string): Promise<void> {
  logAudit('data_erasure_request', userId, { article: 17, reason });

  try {
    // Mark for deletion (don't immediately delete for compliance)
    const userRef = firestore.collection('users').doc(userId);
    await userRef.update({
      markedForDeletion: true,
      deletionReason: reason,
      deletionRequestedAt: new Date(),
      gdprArticle: 17
    });

    // Schedule actual deletion after 30 days (GDPR requirement)
    // In production, use Cloud Scheduler or similar

    // Anonymize chat history instead of deleting
    const chatQuery = firestore.collection('chats').where('userId', '==', userId);
    const chatSnapshot = await chatQuery.get();

    const batch = firestore.batch();
    chatSnapshot.docs.forEach(doc => {
      batch.update(doc.ref, {
        messages: 'anonymized_per_gdpr_article_17',
        userId: 'deleted_user',
        anonymizedAt: new Date()
      });
    });
    await batch.commit();

    logAudit('data_erasure_completed', userId, { recordsAnonymized: chatSnapshot.size });
  } catch (error) {
    logAudit('data_erasure_error', userId, { error: (error as Error).message });
    throw new Error('Failed to process data erasure request');
  }
}

// Article 20: Right to data portability
export async function handleDataPortability(userId: string): Promise<any> {
  logAudit('data_portability_request', userId, { article: 20 });

  try {
    const userDoc = await firestore.collection('users').doc(userId).get();
    const chatHistory = await firestore.collection('chats')
      .where('userId', '==', userId)
      .get();

    // Export in machine-readable format (JSON)
    const portableData = {
      version: '1.0',
      exportType: 'GDPR Article 20 - Data Portability',
      userId: userId,
      exportDate: new Date().toISOString(),
      data: {
        profile: userDoc.data(),
        chats: chatHistory.docs.map(doc => ({
          id: doc.id,
          data: doc.data()
        }))
      },
      metadata: {
        exporter: 'Vertice-Chat SaaS',
        format: 'JSON',
        gdprCompliant: true
      }
    };

    return portableData;
  } catch (error) {
    logAudit('data_portability_error', userId, { error: (error as Error).message });
    throw new Error('Failed to export user data');
  }
}

// Consent management
export async function handleConsentUpdate(userId: string, consents: any): Promise<void> {
  logAudit('consent_update', userId, { consents });

  try {
    await firestore.collection('users').doc(userId).update({
      consents: {
        ...consents,
        updatedAt: new Date(),
        gdprVersion: '2026-01'
      }
    });
  } catch (error) {
    logAudit('consent_update_error', userId, { error: (error as Error).message });
    throw new Error('Failed to update consent preferences');
  }
}

// Data retention enforcement
export async function enforceDataRetention(): Promise<void> {
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  try {
    // Delete old chat history
    const oldChats = await firestore.collection('chats')
      .where('timestamp', '<', thirtyDaysAgo)
      .get();

    const batch = firestore.batch();
    oldChats.docs.forEach(doc => {
      batch.delete(doc.ref);
    });
    await batch.commit();

    logAudit('data_retention_enforced', 'system', { recordsDeleted: oldChats.size });
  } catch (error) {
    logAudit('data_retention_error', 'system', { error: (error as Error).message });
  }
}
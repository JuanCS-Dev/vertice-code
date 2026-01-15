const express = require('express');
const app = express();

// CORS middleware
app.use((req, res, next) => {
  // Allow requests from your frontend domain
  res.header('Access-Control-Allow-Origin', 'https://vertice-frontend-us-239800439060.us-central1.run.app');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

// Parse JSON bodies
app.use(express.json());

app.get('/', (req, res) => {
  res.json({
    message: '🎉 Vertice Enterprise SaaS - Backend Ativo!',
    status: '✅ Operacional',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    cors: '✅ Habilitado',
    frontend_url: 'https://vertice-frontend-us-239800439060.us-central1.run.app'
  });
});

app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    uptime: process.uptime(),
    cors: 'enabled'
  });
});

// Test endpoint for CORS
app.get('/test', (req, res) => {
  res.json({
    success: true,
    message: 'CORS test successful!',
    origin: req.headers.origin || 'unknown',
    timestamp: new Date().toISOString()
  });
});

const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`🚀 Vertice Backend com CORS rodando na porta ${port}`);
});

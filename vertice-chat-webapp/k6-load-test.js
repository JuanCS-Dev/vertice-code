/**
 * Load test for Chat API
 *
 * Tool: k6
 * Reference: https://k6.io/docs/
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp-up
    { duration: '5m', target: 50 },  // Sustained load
    { duration: '2m', target: 100 }, // Peak load
    { duration: '2m', target: 0 },   // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% failures
  },
};

const BASE_URL = 'https://api.vertice.ai';
const AUTH_TOKEN = 'test_token_here';

export default function () {
  const payload = JSON.stringify({
    messages: [{ role: 'user', content: 'Hello!' }],
    stream: false,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
  };

  const res = http.post(`${BASE_URL}/api/v1/chat`, payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has content': (r) => r.json().content.length > 0,
  });

  sleep(1);
}

/**
 * Run load test:
 * k6 run k6-load-test.js
 *
 * Or with custom options:
 * k6 run --vus 10 --duration 30s k6-load-test.js
 */

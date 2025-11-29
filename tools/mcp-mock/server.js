/**
 * Simple MCP mock server for local development.
 * - Endpoints: POST /v1/chat/completions and /v1/completions
 * - Basic API key check via header 'x-api-key' or env var per-server
 * - Concurrency control, timeouts and structured logging (pino)
 * - Graceful shutdown and visibility in terminal
 *
 * Usage:
 *   cd tools/mcp-mock
 *   npm install
 *   MCP_API_KEY=secret npm start
 */

const express = require('express');
const bodyParser = require('body-parser');
const pino = require('pino');
const pLimit = require('p-limit');
const helmet = require('helmet');
const cors = require('cors');

const PORT = process.env.PORT ? Number(process.env.PORT) : 8080;
const API_KEY = process.env.MCP_LOCAL_API_KEY || process.env.MCP_API_KEY || '';
const LOG_LEVEL = process.env.LOG_LEVEL || 'debug';
const MAX_CONCURRENCY = parseInt(process.env.MCP_MAX_CONCURRENCY || '6', 10);
const REQUEST_TIMEOUT_MS = parseInt(process.env.MCP_REQUEST_TIMEOUT_MS || '25000', 10);

const logger = pino({
  level: LOG_LEVEL,
  transport: {
    target: 'pino-pretty',
    options: { colorize: true, translateTime: 'SYS:standard' }
  }
});

const app = express();
app.use(helmet());
app.use(cors());
app.use(bodyParser.json({ limit: '1mb' }));

const limit = pLimit(MAX_CONCURRENCY);

function checkApiKey(req, res) {
  const key = req.header('x-api-key') || req.query.api_key || '';
  if (!API_KEY) {
    // If no local API_KEY configured, accept unauthenticated for dev convenience
    return true;
  }
  return key === API_KEY;
}

// Common handler wrapper with logging, timeout and concurrency limit
function withCommon(handler) {
  return async (req, res) => {
    const start = Date.now();
    const id = Math.random().toString(36).slice(2, 9);
    logger.debug({ id, path: req.path, method: req.method, body: req.body }, 'incoming request');

    if (!checkApiKey(req, res)) {
      logger.warn({ id }, 'unauthorized request');
      return res.status(401).json({ error: 'invalid api key' });
    }

    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      logger.error({ id }, 'request timed out');
      try {
        res.status(504).json({ error: 'request timeout' });
      } catch (e) {
        // ignore
      }
    }, REQUEST_TIMEOUT_MS);

    try {
      await limit(async () => {
        if (timedOut) return;
        await handler(req, res, { id, start });
      });
    } catch (err) {
      logger.error({ id, err: err.message || err }, 'handler error');
      if (!res.headersSent) res.status(500).json({ error: 'internal_server_error', detail: err.message || String(err) });
    } finally {
      clearTimeout(timer);
      const took = Date.now() - start;
      logger.debug({ id, took }, 'request finished');
    }
  };
}

app.post('/v1/chat/completions', withCommon(async (req, res, ctx) => {
  const { id } = ctx;
  const messages = req.body.messages || [];
  // Basic echo mock: concatenates messages and returns a fake completion
  const prompt = messages.map(m => (m.role ? `${m.role}: ${m.content}` : m.content)).join('\n');
  const content = `Mock response (echo): ${prompt.slice(0, 400)}`;

  // Add helpful debug info and slow response if requested via header
  if (req.header('x-mock-delay')) {
    const delay = Math.min(5000, Number(req.header('x-mock-delay')) || 0);
    await new Promise(r => setTimeout(r, delay));
  }

  res.json({
    id: `mock-${Date.now()}`,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: req.body.model || 'mock-model-1',
    choices: [
      {
        index: 0,
        message: { role: 'assistant', content },
        finish_reason: 'stop'
      }
    ],
    usage: {
      prompt_tokens: Math.min(1000, Math.max(1, Math.floor(prompt.length / 4))),
      completion_tokens: Math.min(1000, Math.floor(content.length / 4)),
      total_tokens: Math.min(2000, Math.floor((prompt.length + content.length) / 4))
    }
  });
}));

app.post('/v1/completions', withCommon(async (req, res) => {
  const prompt = req.body.prompt || '';
  const text = `Mock completion: ${prompt.slice(0, 400)}`;
  res.json({
    id: `mock-c-${Date.now()}`,
    object: 'text_completion',
    created: Math.floor(Date.now() / 1000),
    model: req.body.model || 'mock-model-1',
    choices: [{ text, index: 0, finish_reason: 'stop' }],
    usage: {
      prompt_tokens: Math.max(1, Math.floor(prompt.length / 4)),
      completion_tokens: Math.max(1, Math.floor(text.length / 4)),
      total_tokens: Math.max(1, Math.floor((prompt.length + text.length) / 4))
    }
  });
}));

// Health, metrics and graceful shutdown
app.get('/healthz', (req, res) => res.json({ status: 'ok', uptime: process.uptime() }));
app.get('/ready', (req, res) => res.json({ ready: true }));

const server = app.listen(PORT, () => {
  logger.info({ port: PORT, maxConcurrency: MAX_CONCURRENCY }, 'MCP mock server listening');
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down');
  server.close(() => process.exit(0));
});
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down');
  server.close(() => process.exit(0));
});

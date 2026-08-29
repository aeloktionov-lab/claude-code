const express = require('express');
const path = require('path');
const apiRouter = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 3000;
// Change this before deploying to production (env var ADMIN_PASSWORD).
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'change-me';

app.use(express.json());

// Basic auth guard for the admin API only — protects order/lead data.
app.use('/api/admin', (req, res, next) => {
  const auth = req.headers.authorization || '';
  const [scheme, encoded] = auth.split(' ');
  if (scheme !== 'Basic' || !encoded) {
    res.set('WWW-Authenticate', 'Basic realm="admin"');
    return res.status(401).send('Authentication required');
  }
  const [, password] = Buffer.from(encoded, 'base64').toString().split(':');
  if (password !== ADMIN_PASSWORD) {
    res.set('WWW-Authenticate', 'Basic realm="admin"');
    return res.status(401).send('Invalid credentials');
  }
  next();
});

app.use('/api', apiRouter);
app.use(express.static(path.join(__dirname, '..', 'public')));

app.listen(PORT, () => {
  console.log(`croid.ru server running on http://localhost:${PORT}`);
  if (ADMIN_PASSWORD === 'change-me') {
    console.warn('WARNING: using default admin password — set ADMIN_PASSWORD env var before deploying.');
  }
});

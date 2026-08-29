const express = require('express');
const fs = require('fs');
const path = require('path');
const db = require('../db');
const { notifyNewOrder, notifyNewLead } = require('../notify');

const router = express.Router();

const productsPath = path.join(__dirname, '..', '..', 'data', 'products.json');
const configPath = path.join(__dirname, '..', '..', 'data', 'config.json');

function loadJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

// --- Config & products (read-only, sourced from /data) ---

router.get('/config', (req, res) => {
  res.json(loadJson(configPath));
});

router.get('/products', (req, res) => {
  const products = loadJson(productsPath);
  const { category } = req.query;
  const filtered = category ? products.filter((p) => p.category === category) : products;
  res.json(filtered);
});

router.get('/products/:id', (req, res) => {
  const products = loadJson(productsPath);
  const product = products.find((p) => p.id === req.params.id);
  if (!product) return res.status(404).json({ error: 'not_found' });
  res.json(product);
});

// --- Orders ---

function validateOrderBody(body) {
  const errors = [];
  if (!body.company || !body.company.trim()) errors.push('company');
  if (!body.contactName || !body.contactName.trim()) errors.push('contactName');
  if (!body.phone || !body.phone.trim()) errors.push('phone');
  if (!Array.isArray(body.items) || body.items.length === 0) errors.push('items');
  return errors;
}

router.post('/orders', (req, res) => {
  const errors = validateOrderBody(req.body);
  if (errors.length) {
    return res.status(400).json({ error: 'validation', fields: errors });
  }

  const products = loadJson(productsPath);
  const items = req.body.items.map((item) => {
    const product = products.find((p) => p.id === item.id);
    return {
      id: item.id,
      name: product ? product.name : item.id,
      qty: Number(item.qty) || 0,
      size: item.size || null,
      color: item.color || null,
      price: product ? product.price : 0,
    };
  });
  const total = items.reduce((sum, item) => sum + item.price * item.qty, 0);

  const stmt = db.prepare(`
    INSERT INTO orders (company, contact_name, phone, email, comment, items_json, total)
    VALUES (@company, @contact_name, @phone, @email, @comment, @items_json, @total)
  `);
  const info = stmt.run({
    company: req.body.company.trim(),
    contact_name: req.body.contactName.trim(),
    phone: req.body.phone.trim(),
    email: (req.body.email || '').trim(),
    comment: (req.body.comment || '').trim(),
    items_json: JSON.stringify(items),
    total,
  });

  const order = {
    id: info.lastInsertRowid,
    company: req.body.company.trim(),
    contactName: req.body.contactName.trim(),
    phone: req.body.phone.trim(),
    email: (req.body.email || '').trim(),
    comment: (req.body.comment || '').trim(),
    items,
    total,
  };
  notifyNewOrder(order);

  res.status(201).json({ id: info.lastInsertRowid, total });
});

// --- Leads (contact form) ---

router.post('/leads', (req, res) => {
  const { name, phone, email, message } = req.body;
  if (!name || !name.trim()) {
    return res.status(400).json({ error: 'validation', fields: ['name'] });
  }
  const stmt = db.prepare(`
    INSERT INTO leads (name, phone, email, message)
    VALUES (@name, @phone, @email, @message)
  `);
  const info = stmt.run({
    name: name.trim(),
    phone: (phone || '').trim(),
    email: (email || '').trim(),
    message: (message || '').trim(),
  });
  const lead = {
    id: info.lastInsertRowid,
    name: name.trim(),
    phone: (phone || '').trim(),
    email: (email || '').trim(),
    message: (message || '').trim(),
  };
  notifyNewLead(lead);

  res.status(201).json({ id: info.lastInsertRowid });
});

// --- Simple admin read endpoints (protected in index.js) ---

router.get('/admin/orders', (req, res) => {
  const orders = db.prepare('SELECT * FROM orders ORDER BY id DESC').all();
  res.json(orders.map((o) => ({ ...o, items: JSON.parse(o.items_json) })));
});

router.get('/admin/leads', (req, res) => {
  const leads = db.prepare('SELECT * FROM leads ORDER BY id DESC').all();
  res.json(leads);
});

module.exports = router;

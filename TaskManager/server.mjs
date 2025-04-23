// server.js
import express from 'express';
import path from 'path';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import { fileURLToPath } from 'url';

sqlite3.verbose();

const app = express();
const port = 8080;

// Required for ES module path resolution
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Database connection
async function openDb() {
  return await open({
    filename: 'addtasks.db',
    driver: sqlite3.Database
  });
}

let database = null;
openDb()
  .then((result) => {
    database = result;
    console.log("Database opened");

    // Create the enhanced task table
    return database.run(`
      CREATE TABLE IF NOT EXISTS TaskTable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        deadline TEXT NOT NULL,
        priority TEXT NOT NULL,
        category TEXT,
        completed INTEGER DEFAULT 0
      )
    `);
  })
  .catch(console.error);

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public'))); // serve static frontend files

// Serve index.html
app.get('/', function (req, res) {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// GET all tasks
app.get('/api/todos', async (req, res) => {
  try {
    const todos = await database.all('SELECT * FROM TaskTable');
    res.json(todos.map(t => ({
      ...t,
      completed: Boolean(t.completed)
    })));
  } catch (err) {
    console.error(err);
    res.status(500).end();
  }
});

// POST a new task
app.post('/api/todos', async (req, res) => {
  const { title, deadline, priority, category } = req.body;
  if (!title || !deadline || !priority) {
    return res.status(400).send('Title, deadline, and priority are required');
  }

  try {
    const result = await database.run(
      `INSERT INTO TaskTable (title, deadline, priority, category) VALUES (?, ?, ?, ?)`,
      [title, deadline, priority, category]
    );
    res.status(201).json({ id: result.lastID, title, deadline, priority, category, completed: false });
  } catch (err) {
    console.error(err);
    res.status(500).end();
  }
});

// PUT update a task
app.put('/api/todos/:id', async (req, res) => {
  const { id } = req.params;
  const { title, deadline, priority, category, completed } = req.body;

  try {
    await database.run(`
      UPDATE TaskTable SET title=?, deadline=?, priority=?, category=?, completed=?
      WHERE id=?
    `, [title, deadline, priority, category, completed ? 1 : 0, id]);

    res.send('Task updated');
  } catch (err) {
    console.error(err);
    res.status(500).end();
  }
});

// DELETE a task
app.delete('/api/todos/:id', async (req, res) => {
  const { id } = req.params;

  try {
    await database.run(`DELETE FROM TaskTable WHERE id = ?`, [id]);
    res.send('Task deleted');
  } catch (err) {
    console.error(err);
    res.status(500).end();
  }
});

// Start server
app.listen(port, () => {
  console.log(` Server running at http://localhost:${port}`);
});

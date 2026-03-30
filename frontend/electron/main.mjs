import { app, BrowserWindow, protocol } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import electronServe from 'electron-serve';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const isDev = process.env.NODE_ENV !== 'production' && !app.isPackaged;

const loadURL = isDev
  ? (win) => win.loadURL('http://localhost:5173')
  : electronServe({
      directory: path.join(__dirname, '..', 'build')
    });

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.mjs'),
      webSecurity: true
    }
  });

  loadURL(win);
  
  // Open DevTools automatically in dev mode
  if (isDev) {
    win.webContents.openDevTools();
  }
}

app.whenReady().then(() => {
  protocol.registerFileProtocol('local-audio', (request, callback) => {
    const url = request.url;
    const filePath = url.replace('local-audio://', '');
    
    try {
      callback({ path: decodeURIComponent(filePath) });
    } catch (error) {
      callback({ error: error.code });
    }
  });
  
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
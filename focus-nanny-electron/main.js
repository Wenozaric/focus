const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let win, py
function setTitleBarTheme(theme) {
	if (!win || win.isDestroyed()) return
	const dark = theme === 'dark'
	try {
		win.setBackgroundColor(dark ? '#0f172a' : '#f1f5f9')
	} catch {}
	if (process.platform === 'win32' && win.setTitleBarOverlay) {
		try {
			win.setTitleBarOverlay({
				color: dark ? '#0f172a' : '#f1f5f9',
				symbolColor: dark ? '#f1f5f9' : '#0f172a',
				height: 32,
			})
		} catch {}
	}
}
function createWin() {
	const iconPath = path.join(__dirname, 'build', 'icon.png')
	win = new BrowserWindow({
		width: 1020,
		height: 860,
		minWidth: 860,
		minHeight: 720,
		backgroundColor: '#f1f5f9',
		title: 'Focus',
		icon: iconPath,
		titleBarStyle: 'hidden',
		titleBarOverlay: { color: '#f1f5f9', symbolColor: '#0f172a', height: 32 },
		webPreferences: {
			preload: path.join(__dirname, 'preload.js'),
			contextIsolation: true,
			nodeIntegration: false,
		},
	})
	win.loadFile(path.join(__dirname, 'renderer', 'index.html'))
}

function startBridge() {
	const bridge = path.join(__dirname, '..', 'focus-nanny', 'bridge.py')
	const candidates = [
		['py', '-u', bridge, '--jsonl'],
		['python', '-u', bridge, '--jsonl'],
		['python3', '-u', bridge, '--jsonl'],
	]
	let idx = 0
	const trySpawn = () => {
		if (idx >= candidates.length) {
			console.log('[bridge] no python, mock mode')
			return
		}
		const [cmd, ...args] = candidates[idx++]
		py = spawn(cmd, args, { stdio: ['pipe', 'pipe', 'pipe'] })
		let ok = false
		py.stdout.on('data', d => {
			ok = true
			const lines = d.toString().split('\n').filter(Boolean)
			for (const line of lines) {
				try {
					const msg = JSON.parse(line)
					if (win) win.webContents.send('tick', msg)
				} catch {}
			}
		})
		py.stderr.on('data', d => process.stdout.write('[py] ' + d))
		py.on('error', () => {
			py = null
			trySpawn()
		})
		py.on('close', code => {
			if (!ok) {
				py = null
				trySpawn()
			} else console.log('[bridge] exit', code)
		})
		setTimeout(() => {
			if (!ok && py && !py.killed) {
				try {
					py.kill()
				} catch {}
			}
		}, 2500)
	}
	trySpawn()
}

app.whenReady().then(() => {
	createWin()
	startBridge()
	app.on('activate', () => {
		if (BrowserWindow.getAllWindows().length === 0) createWin()
	})
})
app.on('window-all-closed', () => {
	if (process.platform !== 'darwin') app.quit()
})
app.on('before-quit', () => {
	try {
		py && py.kill()
	} catch {}
})

ipcMain.on('set-limits', (_e, data) => {
	if (py && py.stdin.writable)
		py.stdin.write(JSON.stringify({ type: 'set_limits', ...data }) + '\n')
})
ipcMain.on('theme-changed', (_e, theme) => setTitleBarTheme(theme))
ipcMain.on('vision-now', () => {
	if (py && py.stdin.writable)
		py.stdin.write(JSON.stringify({ type: 'vision_now' }) + '\n')
	else if (win)
		win.webContents.send('tick', {
			visionText: '(mock) скрин запрошен',
			verdict: 'MOCK [OTHER] — без Python данные эмулируются',
			visionTag: 'other',
		})
})
ipcMain.on('reset-today', () => {
	if (py && py.stdin.writable)
		py.stdin.write(JSON.stringify({ type: 'reset' }) + '\n')
})

const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('api', {
  onTick: (cb)=> ipcRenderer.on('tick', (_e, data)=>cb(data)),
  setLimits: (data)=> ipcRenderer.send('set-limits', data),
  visionNow: ()=> ipcRenderer.send('vision-now'),
  resetToday: ()=> ipcRenderer.send('reset-today'),
  setTheme: (theme)=> ipcRenderer.send('theme-changed', theme),
});

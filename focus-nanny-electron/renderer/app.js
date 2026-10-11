// theme/palette already set inline in <head> to avoid FOUC
;(function () {
	try {
		var curP = localStorage.getItem('palette') || 'slate'
		document.querySelectorAll('.pal').forEach(function (b) {
			if (b.dataset.palette === curP) {
				document.querySelectorAll('.pal').forEach(function (x) {
					x.classList.remove('active')
				})
				b.classList.add('active')
			}
		})
	} catch (e) {}
})()
const CATS = [
	{ k: 'work', l: 'Работа', c: '#10b981' },
	{ k: 'youtube_edu', l: 'YouTube · учёба', c: '#0ea5e9' },
	{ k: 'youtube', l: 'YouTube', c: '#f59e0b' },
	{ k: 'game', l: 'Игры', c: '#f43f5e' },
	{ k: 'idle', l: 'Простой', c: '#94a3b8' },
	{ k: 'other', l: 'Прочее', c: '#cbd5e1' },
]
const COLOR = {
	work: '#10b981',
	youtube_edu: '#0ea5e9',
	youtube: '#f59e0b',
	game: '#f43f5e',
	idle: '#94a3b8',
	other: '#cbd5e1',
}
let totals = { work: 0, youtube_edu: 0, youtube: 0, game: 0, idle: 0, other: 0 }
let current = 'other'
const els = {
	total: document.getElementById('totalMins'),
	hero: document.getElementById('hero'),
	bars: document.getElementById('bars'),
	exe: document.getElementById('exe'),
	title: document.getElementById('title'),
	vision: document.getElementById('visionText'),
	verdict: document.getElementById('verdict'),
	tag: document.getElementById('tag'),
	meta: document.getElementById('meta'),
	dot: document.getElementById('dot'),
	cat: document.getElementById('catLabel'),
	badge: document.getElementById('badge'),
	clock: document.getElementById('clock'),
}

function renderBars() {
	const total = Object.values(totals).reduce((a, b) => a + b, 0)
	els.total.textContent = Math.round(total) + 'м всего'
	els.hero.textContent =
		Math.floor(total / 60) +
		'ч ' +
		String(Math.round(total % 60)).padStart(2, '0') +
		'м'
	els.bars.innerHTML = ''
	CATS.forEach(cat => {
		const v = totals[cat.k] || 0,
			pct = total > 0 ? v / total : 0,
			active = cat.k === current
		const row = document.createElement('div')
		row.className = 'bar-row'
		row.innerHTML = `<span class="bar-label ${active ? 'active' : ''}"><span class="bar-dot" style="background:${cat.c}"></span>${cat.l}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(pct * 100).toFixed(1)}%;background:${cat.c}"></div></div>
      <span class="bar-val ${active ? 'active' : ''}">${v < 60 ? v.toFixed(1) + 'м' : (v / 60).toFixed(1) + 'ч'}</span>
      <span class="bar-pct ${active ? 'active' : ''}">${Math.round(pct * 100)}%</span>`
		els.bars.appendChild(row)
	})
	els.dot.style.background = COLOR[current] || '#94a3b8'
	els.cat.textContent = current
	els.badge.textContent = current.toUpperCase()
	els.badge.style.background = COLOR[current] || '#cbd5e1'
}

function applyTick(m) {
	if (m.totals) totals = { ...totals, ...m.totals }
	if (m.currentCat) current = m.currentCat
	if (m.exe !== undefined) els.exe.textContent = m.exe || '—'
	if (m.title !== undefined) {
		els.title.textContent = m.title || '—'
		els.meta.textContent = 'заголовок: ' + (m.title || '—')
	}
	if (m.visionText !== undefined) els.vision.textContent = m.visionText || '—'
	if (m.verdict !== undefined) els.verdict.textContent = m.verdict || '—'
	if (m.visionTag !== undefined)
		els.tag.textContent = (m.visionTag || 'other').toUpperCase()
	if (m.limits) {
		/* set slider initial once */
	}
	renderBars()
}

if (window.api) {
	window.api.onTick(applyTick)
}
setInterval(() => {
	els.clock.textContent = new Date().toLocaleTimeString('ru-RU', {
		hour: '2-digit',
		minute: '2-digit',
	})
}, 1000)
renderBars()

// sliders (Fluent + Stepper)
const limits = { game: 30, yt: 30, nag: 5, vol: 35 }
document.querySelectorAll('.row').forEach(row => {
	const key = row.dataset.key,
		min = +row.dataset.min,
		max = +row.dataset.max,
		fmt = row.dataset.fmt
	const track = row.querySelector('.track'),
		fill = row.querySelector('.fill'),
		thumb = row.querySelector('.thumb'),
		val = row.querySelector('.val')
	const minus = row.querySelector('.minus'),
		plus = row.querySelector('.plus')
	const getV = () => limits[key]
	const setV = v => {
		v = Math.max(min, Math.min(max, Math.round(v)))
		limits[key] = v
		update()
		push()
	}
	const fmtVal = v => fmt.replace('%d', v)
	function update() {
		const v = getV(),
			pct = (v - min) / (max - min || 1)
		fill.style.width = pct * 100 + '%'
		thumb.style.left = pct * 100 + '%'
		val.textContent = fmtVal(v)
	}
	function push() {
		if (window.api)
			window.api.setLimits({
				game: limits.game,
				youtube: limits.yt,
				nag: limits.nag,
				volume: limits.vol,
			})
	}
	let drag = false
	function posToVal(clientX) {
		const r = track.getBoundingClientRect()
		const pct = Math.max(0, Math.min(1, (clientX - r.left) / r.width))
		return min + pct * (max - min)
	}
	track.addEventListener('pointerdown', e => {
		drag = true
		track.classList.add('dragging')
		track.setPointerCapture(e.pointerId)
		setV(posToVal(e.clientX))
	})
	track.addEventListener('pointermove', e => {
		if (drag) setV(posToVal(e.clientX))
	})
	track.addEventListener('pointerup', e => {
		drag = false
		track.classList.remove('dragging')
	})
	track.addEventListener('pointerleave', () => {
		track.classList.remove('dragging')
	})
	minus.addEventListener('click', () => setV(getV() - 1))
	plus.addEventListener('click', () => setV(getV() + 1))
	update()
})

// toggles -> push
;['tVoice', 'tPopup', 'tVision'].forEach(id => {
	document.getElementById(id).addEventListener('change', () => {
		const data = {
			voice: document.getElementById('tVoice').checked,
			popup: document.getElementById('tPopup').checked,
			vision: document.getElementById('tVision').checked,
			game: limits.game,
			youtube: limits.yt,
			nag: limits.nag,
			volume: limits.vol,
		}
		if (window.api) window.api.setLimits(data)
	})
})

document
	.getElementById('btnVision')
	.addEventListener('click', () => window.api && window.api.visionNow())
document.getElementById('btnTest').addEventListener('click', () => {
	els.verdict.textContent =
		'Лимит превышен: вы долго занимаетесь отвлечением. Вернитесь к фокусу.'
})
document.getElementById('btnReset').addEventListener('click', () => {
	totals = { work: 0, youtube_edu: 0, youtube: 0, game: 0, idle: 0, other: 0 }
	renderBars()
	if (window.api) window.api.resetToday()
})

;(function(){ try{ var it=document.documentElement.getAttribute('data-theme')||'light'; if(window.api&&window.api.setTheme) window.api.setTheme(it);}catch(e){} })();
// theme + palette
document.getElementById('themeToggle').addEventListener('click', () => {
	const cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'
	document.documentElement.setAttribute('data-theme', cur)
	try { localStorage.setItem('theme', cur) } catch (e) {}
	if(window.api&&window.api.setTheme) window.api.setTheme(cur)
})
document.querySelectorAll('.pal').forEach(b => {
	b.addEventListener('click', () => {
		document.documentElement.setAttribute('data-palette', b.dataset.palette)
		try {
			localStorage.setItem('palette', b.dataset.palette)
		} catch (e) {}
		document.querySelectorAll('.pal').forEach(x => x.classList.remove('active'))
		b.classList.add('active')
	})
})

// mock if no bridge (web preview)
if (!window.api) {
	setInterval(() => {
		current = CATS[Math.floor(Math.random() * CATS.length)].k
		totals[current] = (totals[current] || 0) + 1 / 60
		els.exe.textContent = 'chrome.exe'
		els.title.textContent = 'YouTube — ' + current
		renderBars()
	}, 1000)
}

/* ──────────────────────────────────────────────────────────────────────
   Linite — Landing Page Script
   ────────────────────────────────────────────────────────────────────── */

'use strict';

/* ─── TERMINAL TYPEWRITER ─────────────────────────────────────────────── */
(function initTerminal() {
    const lines = [
        { text: '$ python main.py', color: '#94a3b8' },
        { text: 'Linite v2.0 · Kali GNU/Linux 2025.4 (x86_64)', color: '#7c5af5' },
        { text: 'Package manager: APT · Detected DE: KDE Plasma (Wayland)', color: '#64748b' },
        { text: '', color: '' },
        { text: '⚡ Quick-Start: Developer profile selected (12 apps)', color: '#22d3ee' },
        { text: '🔍 Intelligence Engine: All 10 checks passed ✓', color: '#34d399' },
        { text: '', color: '' },
        { text: '▶ Wave 1 — Installing curl, wget, git …', color: '#e2e8f0' },
        { text: '  [✓] curl       apt install curl            0.8s', color: '#34d399' },
        { text: '  [✓] wget       apt install wget            0.7s', color: '#34d399' },
        { text: '  [✓] git        apt install git             1.2s', color: '#34d399' },
        { text: '', color: '' },
        { text: '▶ Wave 2 — Installing Docker, VS Code, Python 3 …', color: '#e2e8f0' },
        { text: '  [✓] docker     apt install docker.io       4.1s', color: '#34d399' },
        { text: '  [✓] vscode     flatpak install vscode      6.3s', color: '#34d399' },
        { text: '  [✓] python3    apt install python3         0.9s', color: '#34d399' },
        { text: '', color: '' },
        { text: '✅ 12 / 12 apps installed  ·  Total: 28.4s', color: '#34d399' },
        { text: '📜 History written to ~/.config/linite/history.json', color: '#64748b' },
    ];

    const el = document.getElementById('terminal-code');
    if (!el) return;

    let lineIdx = 0, charIdx = 0, output = '';
    const DELAY_CHAR = 18, DELAY_LINE = 120, DELAY_START = 800;

    function typeLine() {
        if (lineIdx >= lines.length) return;
        const { text, color } = lines[lineIdx];
        const body = el.parentElement; /* .terminal-body */
        if (charIdx < text.length) {
            output += `<span style="color:${color || '#e2e8f0'}">${escHtml(text[charIdx])}</span>`;
            el.innerHTML = output + '<span class="cursor">▋</span>';
            body.scrollTop = body.scrollHeight; /* auto-scroll inside fixed box */
            charIdx++;
            setTimeout(typeLine, DELAY_CHAR + (text[charIdx - 1] === ' ' ? 0 : 0));
        } else {
            output += '\n';
            el.innerHTML = output + '<span class="cursor">▋</span>';
            body.scrollTop = body.scrollHeight;
            lineIdx++; charIdx = 0;
            const pause = text === '' ? 60 : DELAY_LINE;
            setTimeout(typeLine, pause);
        }
    }

    function escHtml(t) {
        return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // inject cursor blink style
    const style = document.createElement('style');
    style.textContent = `.cursor{animation:blink .8s step-end infinite}@keyframes blink{50%{opacity:0}}`;
    document.head.appendChild(style);

    setTimeout(typeLine, DELAY_START);
})();

/* ─── NAV SCROLL EFFECT ───────────────────────────────────────────────── */
(function initNav() {
    const nav = document.getElementById('navbar');
    if (!nav) return;
    window.addEventListener('scroll', () => {
        nav.style.boxShadow = window.scrollY > 30
            ? '0 4px 32px rgba(0,0,0,0.5)'
            : '';
    }, { passive: true });
})();

/* ─── SCROLL ANIMATE (IntersectionObserver) ───────────────────────────── */
(function initScrollAnimate() {
    const items = document.querySelectorAll('[data-animate]');
    if (!items.length) return;
    const obs = new IntersectionObserver(entries => {
        entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
    }, { threshold: 0.12 });
    items.forEach(el => obs.observe(el));
})();

/* ─── PROFILE TABS ────────────────────────────────────────────────────── */
(function initProfileTabs() {
    const tabs = document.querySelectorAll('.profile-tab');
    const panes = document.querySelectorAll('.profile-pane');
    if (!tabs.length) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const pane = document.getElementById('pane-' + tab.dataset.profile);
            if (pane) pane.classList.add('active');
        });
    });
})();

/* ─── CATALOG GRID ────────────────────────────────────────────────────── */
(function initCatalog() {
    const grid = document.getElementById('catalog-grid');
    if (!grid) return;

    const categories = [
        {
            icon: '🌐', name: 'Web Browsers', count: 7,
            apps: ['Firefox', 'Chromium', 'Brave', 'Chrome', 'Opera', 'Tor Browser', 'Vivaldi']
        },
        {
            icon: '💻', name: 'Development', count: 8,
            apps: ['VS Code', 'Git', 'Python 3', 'Node.js', 'Docker', 'Vim', 'Neovim', 'GitHub CLI']
        },
        {
            icon: '🎵', name: 'Media', count: 6,
            apps: ['VLC', 'Spotify', 'mpv', 'OBS Studio', 'Audacity', 'HandBrake']
        },
        {
            icon: '💬', name: 'Communication', count: 5,
            apps: ['Discord', 'Telegram', 'Slack', 'Zoom', 'Dropbox']
        },
        {
            icon: '🔧', name: 'Utilities', count: 10,
            apps: ['htop', 'curl', 'wget', '7-Zip', 'Timeshift', 'Flatpak', 'Neofetch', 'Flameshot']
        },
        {
            icon: '📄', name: 'Office', count: 6,
            apps: ['LibreOffice', 'Thunderbird', 'Okular', 'Evince', 'Foxit Reader', 'OpenOffice']
        },
        {
            icon: '🎮', name: 'Gaming', count: 7,
            apps: ['Steam', 'Lutris', 'Heroic', 'Bottles', 'GameMode', 'MangoHud', 'ProtonUp-Qt']
        },
        {
            icon: '🎨', name: 'Graphics', count: 3,
            apps: ['GIMP', 'Inkscape', 'Blender']
        },
        {
            icon: '🌊', name: 'Torrents', count: 4,
            apps: ['qBittorrent', 'Deluge', 'Transmission', 'qBittorrent-nox']
        },
        {
            icon: '🖥️', name: 'Virtualization', count: 3,
            apps: ['VirtualBox', 'VMware', 'QEMU']
        },
        {
            icon: '☕', name: 'Java', count: 5,
            apps: ['OpenJDK', 'Eclipse Temurin', 'Amazon Corretto', 'Zulu JDK', 'Oracle JDK']
        },
        {
            icon: '🔐', name: 'Security', count: 10,
            apps: ['Nmap', 'Metasploit', 'Burp Suite', 'SQLMap', 'Hydra', 'Hashcat']
        },
        {
            icon: '🔒', name: 'Password Managers', count: 3,
            apps: ['Bitwarden', 'KeePassXC', '1Password']
        },
        {
            icon: '🎬', name: 'Video Editors', count: 3,
            apps: ['Kdenlive', 'Shotcut', 'OpenShot']
        },
        {
            icon: '📝', name: 'Note Taking', count: 4,
            apps: ['Obsidian', 'Joplin', 'Logseq', 'CherryTree']
        },
        {
            icon: '🖦', name: 'Terminal Emulators', count: 4,
            apps: ['Alacritty', 'Kitty', 'WezTerm', 'Tilix']
        },
        {
            icon: '🛡️', name: 'VPN', count: 4,
            apps: ['ProtonVPN', 'Mullvad', 'WireGuard', 'OpenVPN']
        },
    ];

    grid.innerHTML = categories.map(cat => `
    <div class="catalog-card">
      <div class="catalog-card-icon">${cat.icon}</div>
      <div class="catalog-card-name">${cat.name}</div>
      <div class="catalog-card-count"><span class="dot"></span>${cat.count} apps</div>
      <div class="catalog-card-apps">
        ${cat.apps.slice(0, 4).map(a => `<span class="catalog-app-tag">${a}</span>`).join('')}
        ${cat.apps.length > 4 ? `<span class="catalog-app-tag">+${cat.apps.length - 4}</span>` : ''}
      </div>
    </div>
  `).join('');
})();

/* ─── GALLERY SLIDER ──────────────────────────────────────────────────── */
(function initGallery() {
    const track = document.getElementById('gallery-track');
    const dots = document.getElementById('gallery-dots');
    const prev = document.getElementById('gallery-prev');
    const next = document.getElementById('gallery-next');
    if (!track || !dots || !prev || !next) return;

    const slides = track.querySelectorAll('.gallery-slide');
    const total = slides.length;
    let current = 0;
    let autoplay = null;

    // Build dots
    for (let i = 0; i < total; i++) {
        const d = document.createElement('button');
        d.className = 'gallery-dot' + (i === 0 ? ' active' : '');
        d.setAttribute('aria-label', 'Slide ' + (i + 1));
        d.addEventListener('click', () => goTo(i));
        dots.appendChild(d);
    }

    // Scroll only within the horizontal track — never touches page scroll
    function goTo(idx) {
        current = (idx + total) % total;
        const slide = slides[current];
        const trackRect = track.getBoundingClientRect();
        const slideRect = slide.getBoundingClientRect();
        const target = slideRect.left - trackRect.left + track.scrollLeft
            - (trackRect.width - slideRect.width) / 2;
        track.scrollTo({ left: target, behavior: 'smooth' });
        dots.querySelectorAll('.gallery-dot')
            .forEach((d, i) => d.classList.toggle('active', i === current));
    }

    prev.addEventListener('click', () => goTo(current - 1));
    next.addEventListener('click', () => goTo(current + 1));

    function startAutoplay() {
        clearInterval(autoplay);
        autoplay = setInterval(() => goTo(current + 1), 4200);
    }

    // Pause on hover
    track.addEventListener('mouseenter', () => clearInterval(autoplay));
    track.addEventListener('mouseleave', startAutoplay);

    // Only start autoplay once gallery section is scrolled into view
    // — prevents it from ever yanking the page on load/refresh
    const sectionObs = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
            if (e.isIntersecting) { startAutoplay(); }
            else { clearInterval(autoplay); }
        });
    }, { threshold: 0.2 });
    var gallerySection = document.getElementById('gallery');
    if (gallerySection) sectionObs.observe(gallerySection);

    // Update active dot when user manually swipes the track
    const slideObs = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
            if (e.isIntersecting) {
                var idx = Array.from(slides).indexOf(e.target);
                if (idx >= 0) {
                    current = idx;
                    dots.querySelectorAll('.gallery-dot')
                        .forEach(function (d, i) { d.classList.toggle('active', i === current); });
                }
            }
        });
    }, { root: track, threshold: 0.5 });
    slides.forEach(function (s) { slideObs.observe(s); });
})();

/* ─── INSTALL DISTRO TABS ─────────────────────────────────────────────── */
(function initInstallTabs() {
    const tabs = document.querySelectorAll('.code-tab');
    if (!tabs.length) return;
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // deactivate siblings
            tab.closest('.install-body').querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
            tab.closest('.install-body').querySelectorAll('.code-panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const panel = document.getElementById('panel-' + tab.dataset.distro);
            if (panel) panel.classList.add('active');
        });
    });
})();

/* ─── COPY BUTTONS ────────────────────────────────────────────────────── */
(function initCopyBtns() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const text = btn.dataset.copy;
            try {
                await navigator.clipboard.writeText(text);
            } catch {
                // fallback
                const ta = document.createElement('textarea');
                ta.value = text; ta.style.position = 'fixed';
                document.body.appendChild(ta); ta.select();
                document.execCommand('copy'); document.body.removeChild(ta);
            }
            const orig = btn.textContent;
            btn.textContent = '✓ Copied!';
            btn.classList.add('copied');
            setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2000);
        });
    });
})();

/* ─── SMOOTH NAV ACTIVE SECTION ───────────────────────────────────────── */
(function initActiveLink() {
    const sections = document.querySelectorAll('section[id]');
    const links = document.querySelectorAll('.nav-links a');
    if (!sections.length || !links.length) return;

    const obs = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                links.forEach(l => {
                    l.style.color = l.getAttribute('href') === '#' + e.target.id
                        ? 'var(--purple-l)' : '';
                });
            }
        });
    }, { threshold: 0.4 });
    sections.forEach(s => obs.observe(s));
})();

/* ─── SCROLL PROGRESS BAR ────────────────────────────────────────────── */
(function initScrollProgress() {
    const bar = document.getElementById('scroll-progress');
    if (!bar) return;
    window.addEventListener('scroll', () => {
        const doc = document.documentElement;
        const scrolled = doc.scrollTop || document.body.scrollTop;
        const total = doc.scrollHeight - doc.clientHeight;
        bar.style.width = total > 0 ? (scrolled / total * 100) + '%' : '0%';
    }, { passive: true });
})();

/* ─── NAVBAR SCROLLED CLASS ──────────────────────────────────────────── */
(function initNavbarScroll() {
    const nav = document.getElementById('navbar');
    if (!nav) return;
    window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.scrollY > 30);
    }, { passive: true });
})();

/* ─── STAT COUNTER ANIMATION ─────────────────────────────────────────── */
(function initStatCounters() {
    const stats = [
        { id: null, selector: '.stat-card:nth-child(1) .stat-num', target: 90, suffix: '+' },
        { id: null, selector: '.stat-card:nth-child(3) .stat-num', target: 17, suffix: '' },
        { id: null, selector: '.stat-card:nth-child(5) .stat-num', target: 6, suffix: '' },
        { id: null, selector: '.stat-card:nth-child(7) .stat-num', target: 0, suffix: '' },
    ];

    function animateCount(el, target, suffix, duration) {
        if (target === 0) { el.textContent = '0' + suffix; return; }
        const start = performance.now();
        function step(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(eased * target) + suffix;
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    const heroStats = document.querySelector('.hero-stats');
    if (!heroStats) return;

    let fired = false;
    const obs = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting && !fired) {
                fired = true;
                stats.forEach(s => {
                    const el = document.querySelector(s.selector);
                    if (el) animateCount(el, s.target, s.suffix, 1400);
                });
            }
        });
    }, { threshold: 0.5 });
    obs.observe(heroStats);
})();

/* ══════════════════════════════════════════════════════════════════════
   INTERACTIVE MOCK WINDOW — full catalog, category filtering, state
   ══════════════════════════════════════════════════════════════════════ */
(function initMockWindow() {

    /* ── App catalog ──────────────────────────────────────────────────── */
    const APPS = [
        /* Development */
        { id: 'vscode', cat: 'dev', icon: '💻', name: 'VS Code', checked: true },
        { id: 'docker', cat: 'dev', icon: '🐳', name: 'Docker', checked: true },
        { id: 'git', cat: 'dev', icon: '🔀', name: 'Git', checked: true },
        { id: 'nodejs', cat: 'dev', icon: '🟢', name: 'Node.js', checked: false },
        { id: 'python', cat: 'dev', icon: '🐍', name: 'Python 3', checked: false },
        { id: 'pycharm', cat: 'dev', icon: '🧠', name: 'PyCharm', checked: false },
        { id: 'postman', cat: 'dev', icon: '📬', name: 'Postman', checked: false },
        { id: 'neovim', cat: 'dev', icon: '📝', name: 'Neovim', checked: false },
        { id: 'github-cli', cat: 'dev', icon: '🐙', name: 'GitHub CLI', checked: false },
        { id: 'kubectl', cat: 'dev', icon: '☸️', name: 'kubectl', checked: false },

        /* Media */
        { id: 'vlc', cat: 'media', icon: '🎬', name: 'VLC', checked: false },
        { id: 'obs', cat: 'media', icon: '📽️', name: 'OBS Studio', checked: true },
        { id: 'gimp', cat: 'media', icon: '🖼️', name: 'GIMP', checked: false },
        { id: 'blender', cat: 'media', icon: '🌀', name: 'Blender', checked: false },
        { id: 'inkscape', cat: 'media', icon: '✏️', name: 'Inkscape', checked: false },
        { id: 'audacity', cat: 'media', icon: '🎙️', name: 'Audacity', checked: false },
        { id: 'kdenlive', cat: 'media', icon: '🎞️', name: 'Kdenlive', checked: false },
        { id: 'spotify', cat: 'media', icon: '🎵', name: 'Spotify', checked: false },

        /* Utilities */
        { id: 'firefox', cat: 'util', icon: '🦊', name: 'Firefox', checked: false },
        { id: 'chromium', cat: 'util', icon: '🌐', name: 'Chromium', checked: false },
        { id: 'telegram', cat: 'util', icon: '✈️', name: 'Telegram', checked: true },
        { id: 'thunderbird', cat: 'util', icon: '🦅', name: 'Thunderbird', checked: false },
        { id: 'zoom', cat: 'util', icon: '📹', name: 'Zoom', checked: false },
        { id: 'timeshift', cat: 'util', icon: '⏱️', name: 'Timeshift', checked: false },
        { id: 'flameshot', cat: 'util', icon: '📸', name: 'Flameshot', checked: false },
        { id: 'keepassxc', cat: 'util', icon: '🔑', name: 'KeePassXC', checked: false },
        { id: 'filezilla', cat: 'util', icon: '📂', name: 'FileZilla', checked: false },

        /* Gaming */
        { id: 'steam', cat: 'gaming', icon: '🎮', name: 'Steam', checked: true },
        { id: 'lutris', cat: 'gaming', icon: '🏆', name: 'Lutris', checked: false },
        { id: 'discord', cat: 'gaming', icon: '🎙️', name: 'Discord', checked: false },
        { id: 'bottles', cat: 'gaming', icon: '🍾', name: 'Bottles', checked: false },
        { id: 'heroic', cat: 'gaming', icon: '⚡', name: 'Heroic Launcher', checked: false },
        { id: 'mangohud', cat: 'gaming', icon: '📊', name: 'MangoHud', checked: false },

        /* Security */
        { id: 'nmap', cat: 'sec', icon: '🗺️', name: 'Nmap', checked: false },
        { id: 'wireshark', cat: 'sec', icon: '🦈', name: 'Wireshark', checked: true },
        { id: 'metasploit', cat: 'sec', icon: '💀', name: 'Metasploit', checked: false },
        { id: 'hashcat', cat: 'sec', icon: '🔓', name: 'Hashcat', checked: false },
        { id: 'burpsuite', cat: 'sec', icon: '🕷️', name: 'Burp Suite', checked: false },
        { id: 'john', cat: 'sec', icon: '⚒️', name: 'John the Ripper', checked: false },
        { id: 'aircrack', cat: 'sec', icon: '📡', name: 'Aircrack-ng', checked: false },
    ];

    /* State map: id → checked */
    const state = {};
    APPS.forEach(a => { state[a.id] = a.checked; });

    let currentCat = 'all';

    /* ── DOM refs ─────────────────────────────────────────────────────── */
    const content = document.getElementById('mock-content');
    const btn = document.getElementById('mock-install-btn');
    const sideList = document.getElementById('mock-sidebar-list');
    if (!content || !btn || !sideList) return;

    /* ── Render app grid for current category ─────────────────────────── */
    function render() {
        const visible = currentCat === 'all'
            ? APPS
            : APPS.filter(a => a.cat === currentCat);

        content.innerHTML = visible.map(a => `
            <label class="app-item${state[a.id] ? ' checked' : ''}" data-id="${a.id}">
                <input type="checkbox" ${state[a.id] ? 'checked' : ''}>
                <span>${a.icon} ${a.name}</span>
            </label>
        `).join('');

        /* Bind checkbox changes */
        content.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', () => {
                const id = cb.closest('.app-item').dataset.id;
                state[id] = cb.checked;
                cb.closest('.app-item').classList.toggle('checked', cb.checked);
                updateBtn();
            });
        });

        updateBtn();
    }

    /* ── Update install button label ──────────────────────────────────── */
    function updateBtn() {
        const total = Object.values(state).filter(Boolean).length;
        if (total === 0) {
            btn.textContent = 'Select Apps';
            btn.disabled = true;
        } else {
            btn.textContent = `Install ${total} App${total > 1 ? 's' : ''}`;
            btn.disabled = false;
            btn.classList.remove('done');
        }
    }

    /* ── Sidebar category switching ───────────────────────────────────── */
    sideList.addEventListener('click', e => {
        const li = e.target.closest('.mock-cat');
        if (!li) return;
        sideList.querySelectorAll('.mock-cat').forEach(el => el.classList.remove('active'));
        li.classList.add('active');
        currentCat = li.dataset.cat;
        render();
    });

    /* ── Install button animation ─────────────────────────────────────── */
    btn.addEventListener('click', function () {
        if (this.disabled) return;
        const orig = this.textContent;
        this.textContent = '⏳ Installing…';
        this.disabled = true;
        setTimeout(() => {
            this.textContent = '✓ Done!';
            this.classList.add('done');
            this.disabled = false;
            setTimeout(() => {
                this.textContent = orig;
                this.classList.remove('done');
            }, 3000);
        }, 1800);
    });

    /* ── Remove old global stubs so there's no conflict ──────────────── */
    window.mockUpdateBtn = updateBtn;
    window.mockInstall = () => btn.click();

    /* ── Initial render ───────────────────────────────────────────────── */
    render();
})();

/* ══════════════════════════════════════════════════════════════════════
   INTERACTIVE TERMINAL ENGINE  (#iterm-wrap)
   ══════════════════════════════════════════════════════════════════════ */
(function initIterm() {
    const output = document.getElementById('iterm-output');
    const input = document.getElementById('iterm-input');
    const wrap = document.getElementById('iterm-wrap');
    if (!output || !input) return;

    /* ── Command registry ─────────────────────────────────────────────── */
    const COMMANDS = {
        help: () => [
            ['accent', '╔══════════════════════════════════════╗'],
            ['accent', '║     Linite Interactive Terminal       ║'],
            ['accent', '╚══════════════════════════════════════╝'],
            ['blank', ''],
            ['info', 'Available commands:'],
            ['ok', '  help              Show this help message'],
            ['ok', '  list              List all available apps'],
            ['ok', '  list dev          List apps in a category'],
            ['ok', '  install <app>     Simulate installing an app'],
            ['ok', '  update            Simulate full system update'],
            ['ok', '  version           Show Linite version'],
            ['ok', '  distro            Show detected distro info'],
            ['ok', '  profiles          List quick-start profiles'],
            ['ok', '  whoami            Show current user'],
            ['ok', '  uname -a          Show system info'],
            ['ok', '  clear             Clear the terminal'],
            ['ok', '  echo <text>       Echo text back'],
            ['blank', ''],
        ],

        version: () => [
            ['info', 'Linite v2.1.0 — The Ninite for Linux 🐧'],
            ['info', 'Python 3.11.9 · Tkinter 8.6'],
            ['info', 'License: MIT · github.com/Srijan-XI/Linite'],
        ],

        whoami: () => [['ok', 'root@kali']],

        'uname -a': () => [
            ['info', 'Linux kali 6.12.0-kali4-amd64 #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux'],
        ],

        distro: () => [
            ['accent', '── System Detection ──────────────────────'],
            ['ok', '  OS       : Kali Linux 2025.4 (rolling)'],
            ['ok', '  Arch     : x86_64'],
            ['ok', '  DE       : KDE Plasma (Wayland)'],
            ['ok', '  RAM      : 16 GB  (threshold OK)'],
            ['ok', '  GPU      : NVIDIA RTX 3060 (proprietary ✓)'],
            ['ok', '  PM       : apt (primary) · flatpak · snap'],
            ['ok', '  VM       : No (bare metal)'],
        ],

        list: () => [
            ['accent', '── Available Apps (37) ───────────────────'],
            ['info', '  DEVELOPMENT  VS Code, Docker, Git, Node.js, Python 3, PyCharm, Postman, Neovim, GitHub CLI, kubectl'],
            ['info', '  MEDIA        VLC, OBS Studio, GIMP, Blender, Inkscape, Audacity, Kdenlive, Spotify'],
            ['info', '  UTILITIES    Firefox, Chromium, Telegram, Thunderbird, Zoom, Timeshift, Flameshot, KeePassXC, FileZilla'],
            ['info', '  GAMING       Steam, Lutris, Discord, Bottles, Heroic, MangoHud'],
            ['info', '  SECURITY     Nmap, Wireshark, Metasploit, Hashcat, Burp Suite, John, Aircrack-ng'],
            ['blank', ''],
            ['info', 'Usage:  install <appname>   e.g.  install vlc'],
        ],

        'list dev': () => [['info', 'Development: VS Code, Docker, Git, Node.js, Python 3, PyCharm, Postman, Neovim, GitHub CLI, kubectl']],
        'list media': () => [['info', 'Media: VLC, OBS Studio, GIMP, Blender, Inkscape, Audacity, Kdenlive, Spotify']],
        'list util': () => [['info', 'Utilities: Firefox, Chromium, Telegram, Thunderbird, Zoom, Timeshift, Flameshot, KeePassXC, FileZilla']],
        'list gaming': () => [['info', 'Gaming: Steam, Lutris, Discord, Bottles, Heroic Launcher, MangoHud']],
        'list sec': () => [['info', 'Security: Nmap, Wireshark, Metasploit, Hashcat, Burp Suite, John the Ripper, Aircrack-ng']],

        update: () => [
            ['info', '[INFO] Running native PM update (apt upgrade)...'],
            ['ok', '[OK]   apt: 142 packages upgraded.'],
            ['info', '[INFO] Running flatpak update...'],
            ['ok', '[OK]   flatpak: 3 runtimes updated.'],
            ['info', '[INFO] Running snap refresh...'],
            ['ok', '[OK]   snap: up to date.'],
            ['blank', ''],
            ['ok', '✓ System is fully up to date.'],
        ],

        profiles: () => [
            ['accent', '── Quick-Start Profiles ──────────────────'],
            ['ok', '  💻 developer    12 apps  │ Enable Docker daemon, docker group'],
            ['ok', '  🎬 creator      10 apps  │ v4l2loopback, realtime audio'],
            ['ok', '  🔐 pentester    12 apps  │ msfdb init, wireshark group'],
            ['ok', '  🎮 gamer         9 apps  │ Steam multilib, GameMode'],
            ['ok', '  🎓 student       11 apps  │ Enable Flatpak'],
            ['ok', '  🏠 daily         11 apps  │ Timeshift cron'],
        ],

        clear: () => 'CLEAR',
    };

    /* Valid app names for install simulation */
    const KNOWN_APPS = ['vlc', 'docker', 'git', 'nodejs', 'python', 'firefox', 'steam', 'obs', 'gimp', 'blender',
        'vscode', 'code', 'neovim', 'postman', 'spotify', 'telegram', 'discord', 'lutris', 'nmap', 'wireshark',
        'metasploit', 'hashcat', 'aircrack', 'burpsuite', 'chromium', 'zoom', 'timeshift', 'flameshot', 'keepassxc',
        'filezilla', 'audacity', 'inkscape', 'kdenlive', 'bottles', 'heroic', 'mangohud', 'pycharm', 'thunderbird'];

    const ALL_CMDS = [...Object.keys(COMMANDS),
    ...KNOWN_APPS.map(a => 'install ' + a), 'echo'];

    /* ── Command history ──────────────────────────────────────────────── */
    let history = [], histIdx = -1;

    /* ── Output helpers ───────────────────────────────────────────────── */
    function addLine(type, text) {
        const s = document.createElement('span');
        s.className = `iterm-line ${type}`;
        s.textContent = text;
        output.appendChild(s);
        output.scrollTop = output.scrollHeight;
    }

    /* Stream lines with a small per-line delay for "typing" feel */
    function stream(lines, delay = 55) {
        lines.forEach(([type, text], i) => {
            setTimeout(() => addLine(type, text), i * delay);
        });
    }

    /* ── Process command ──────────────────────────────────────────────── */
    function run(raw) {
        const cmd = raw.trim();
        if (!cmd) return;

        /* echo the command */
        addLine('cmd', cmd);

        /* history */
        history.unshift(cmd);
        if (history.length > 50) history.pop();
        histIdx = -1;

        /* clear */
        if (cmd === 'clear') { output.innerHTML = ''; return; }

        /* install <app> */
        const installMatch = cmd.match(/^(?:linite\s+)?(?:--cli\s+)?install\s+(.+)/i);
        if (installMatch) {
            const app = installMatch[1].trim().toLowerCase().replace(/\s+/g, '-');
            const known = KNOWN_APPS.some(a => a === app || app.includes(a) || a.includes(app));
            if (known) {
                stream([
                    ['info', `[INFO] Resolving package: ${app}`],
                    ['info', `[INFO] Package manager: apt`],
                    ['info', `[INFO] Downloading ${app}...`],
                    ['ok', `[OK]   Installing ${app}...       [SUCCESS]`],
                    ['ok', `[OK]   Post-install tweaks applied.`],
                    ['blank', ''],
                    ['ok', `✓ ${app} installed successfully!`],
                ]);
            } else {
                stream([
                    ['warn', `[WARN] '${app}' not found in Linite catalog.`],
                    ['info', '       Run:  list  to see all available apps.'],
                ]);
            }
            return;
        }

        /* echo */
        if (cmd.startsWith('echo ')) {
            addLine('info', cmd.slice(5));
            return;
        }

        /* linite prefix passthrough */
        const stripped = cmd.replace(/^linite\s+(--cli\s+)?/, '');

        const handler = COMMANDS[cmd] || COMMANDS[stripped];
        if (handler) {
            const result = handler();
            if (result !== 'CLEAR') stream(result);
        } else {
            stream([
                ['err', `bash: ${cmd}: command not found`],
                ['info', `       Type  help  to see available commands.`],
            ]);
        }
    }

    /* ── Keyboard handling ────────────────────────────────────────────── */
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            run(input.value);
            input.value = '';
        }
        else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (histIdx < history.length - 1) { histIdx++; input.value = history[histIdx]; }
        }
        else if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (histIdx > 0) { histIdx--; input.value = history[histIdx]; }
            else { histIdx = -1; input.value = ''; }
        }
        else if (e.key === 'Tab') {
            e.preventDefault();
            const val = input.value.toLowerCase();
            const match = ALL_CMDS.find(c => c.startsWith(val) && c !== val);
            if (match) input.value = match;
        }
    });

    /* Click anywhere in the wrap → focus input */
    wrap.addEventListener('click', () => input.focus());

    /* ── Welcome splash ───────────────────────────────────────────────── */
    stream([
        ['accent', 'Linite v2.1.0 — Interactive Shell 🐧'],
        ['info', 'Type  help  to see all commands. Tab to autocomplete.'],
        ['blank', ''],
    ], 30);
})();

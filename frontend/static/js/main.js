/* ============================================================
   U-RIDE — main.js
   Funciones generales de la aplicación
   ============================================================ */

// ── Sidebar Toggle ───────────────────────────────────────────
function toggleSidebar() {
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        document.body.classList.toggle('mobile-nav-open');
    } else {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebar-collapsed', document.body.classList.contains('sidebar-collapsed'));
    }
    
    const icon = document.querySelector('#sidebarToggle i');
    if (icon) {
        // En móvil: si está abierto (mobile-nav-open), mostrar X.
        // En desktop: si está colapsado (sidebar-collapsed), mostrar barras.
        if (isMobile) {
            icon.className = document.body.classList.contains('mobile-nav-open') ? 'fas fa-times' : 'fas fa-bars';
        } else {
            icon.className = document.body.classList.contains('sidebar-collapsed') ? 'fas fa-bars' : 'fas fa-times';
        }
    }
}

// Restaurar estado del sidebar al cargar
(function () {
    const isMobile = window.innerWidth <= 768;
    if (!isMobile) {
        if (localStorage.getItem('sidebar-collapsed') === 'true') {
            document.body.classList.add('sidebar-collapsed');
            const icon = document.querySelector('#sidebarToggle i');
            if (icon) icon.className = 'fas fa-bars';
        } else {
            const icon = document.querySelector('#sidebarToggle i');
            if (icon) icon.className = 'fas fa-times';
        }
    } else {
        const icon = document.querySelector('#sidebarToggle i');
        if (icon) icon.className = 'fas fa-bars';
    }
})();

// Cerrar sidebar al hacer click en link (solo móvil)
document.addEventListener('click', function(e) {
    if (window.innerWidth <= 768 && e.target.closest('.nav-link-item')) {
        document.body.classList.remove('mobile-nav-open');
        const icon = document.querySelector('#sidebarToggle i');
        if (icon) icon.className = 'fas fa-bars';
    }
});

// ── Auto-dismiss flash messages ──────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.flash-alert').forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity .4s';
            el.style.opacity = '0';
            setTimeout(function () { el.remove(); }, 400);
        }, 5000);
    });
});

// ── Confirm actions ──────────────────────────────────────────
function confirmAction(msg) {
    return confirm(msg || '¿Estás seguro de realizar esta acción?');
}

// ── Fetch helper ─────────────────────────────────────────────
async function urideFetch(url, options = {}) {
    try {
        const resp = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return await resp.json();
    } catch (e) {
        console.error('[U-Ride] Fetch error:', e);
        return null;
    }
}

// ── Datetime local min (formularios) ────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    const dtInputs = document.querySelectorAll('input[type="datetime-local"]');
    if (dtInputs.length) {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset() + 60);
        const min = now.toISOString().slice(0, 16);
        dtInputs.forEach(inp => { inp.min = min; });
    }
});

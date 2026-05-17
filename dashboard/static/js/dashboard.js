document.addEventListener('DOMContentLoaded', function() {
    var menuBtn = document.getElementById('mobileMenuBtn');
    var closeBtn = document.getElementById('closeMenuBtn');
    var mobileMenu = document.getElementById('mobileMenu');
    if (menuBtn && mobileMenu) {
        menuBtn.addEventListener('click', function() { mobileMenu.classList.remove('hidden'); });
        if (closeBtn) closeBtn.addEventListener('click', function() { mobileMenu.classList.add('hidden'); });
        mobileMenu.addEventListener('click', function(e) { if (e.target === mobileMenu) mobileMenu.classList.add('hidden'); });
    }
    var dot = document.getElementById('statusDot');
    var txt = document.getElementById('statusText');
    if (dot && txt) {
        fetch((typeof API !== 'undefined' ? API : 'http://localhost:8080') + '/api/stats').then(function(r){return r.json();}).then(function(d){
            var ok = d.bots && d.bots.length > 0;
            dot.className = 'w-2 h-2 rounded-full ' + (ok ? 'bg-green-500 animate-pulse' : 'bg-red-500');
            txt.textContent = ok ? 'Online' : 'Offline';
        }).catch(function(){ dot.className = 'w-2 h-2 rounded-full bg-red-500'; txt.textContent = 'Offline'; });
    }
});

document.addEventListener('DOMContentLoaded', () => {
  const mobileToggle = document.getElementById('btn-mobile-toggle');
  const navMenu = document.getElementById('nav-menu');
  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      navMenu.classList.toggle('show-mobile');
    });
    document.addEventListener('click', (e) => {
      if (!navMenu.contains(e.target) && !mobileToggle.contains(e.target)) {
        navMenu.classList.remove('show-mobile');
      }
    });
  }
  const pageSwitchBtn = document.getElementById('btn-page-switch');
  const pageSwitchDropdown = document.getElementById('page-switch-menu');
  if (pageSwitchBtn && pageSwitchDropdown) {
    pageSwitchBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      pageSwitchDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!pageSwitchDropdown.contains(e.target) && !pageSwitchBtn.contains(e.target)) {
        pageSwitchDropdown.classList.remove('show');
      }
    });
  }

  const userBtn = document.getElementById('user-profile-btn');
  const userDropdown = document.getElementById('user-profile-menu');

  if (userBtn && userDropdown) {
    userBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!userDropdown.contains(e.target) && !userBtn.contains(e.target)) {
        userDropdown.classList.remove('show');
      }
    });
  }
  document.querySelectorAll('.flash-close').forEach(btn => {
    btn.addEventListener('click', function() {
      const flash = this.closest('.flash-message');
      if (flash) {
        flash.style.opacity = '0';
        flash.style.transform = 'translateY(-10px)';
        setTimeout(() => flash.remove(), 250);
      }
    });
  });
});

function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const iconSvg = type === 'success'
    ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`
    : type === 'error'
    ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`
    : `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;

  toast.innerHTML = `
    ${iconSvg}
    <div class="toast-message">${message}</div>
    <button class="toast-close-btn" onclick="this.parentElement.remove()">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
    </button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(30px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

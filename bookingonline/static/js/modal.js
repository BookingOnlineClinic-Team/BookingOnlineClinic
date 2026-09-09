function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.remove('active');
  document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });

    const closeBtn = modal.querySelector('.modal-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => closeModal(modal.id));
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(modal => {
        closeModal(modal.id);
      });
    }
  });
});

function showStatusModal({ title, message, type = 'warning', confirmText = 'Đồng ý', cancelText = 'Đóng', onConfirm }) {
  let modal = document.getElementById('generic-status-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'generic-status-modal';
    modal.className = 'modal-backdrop';
    document.body.appendChild(modal);
  }

  const iconSvgMap = {
    warning: `<div class="status-modal-icon icon-warning"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg></div>`,
    error: `<div class="status-modal-icon icon-error"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg></div>`,
    success: `<div class="status-modal-icon icon-success"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg></div>`,
    confirm: `<div class="status-modal-icon icon-confirm"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></div>`
  };

  modal.innerHTML = `
    <div class="modal-dialog modal-sm">
      <div class="modal-body status-modal-content">
        ${iconSvgMap[type] || iconSvgMap.warning}
        <h3 class="status-modal-title">${title}</h3>
        <p class="status-modal-desc">${message}</p>
        <div class="status-modal-actions">
          ${cancelText ? `<button class="btn btn-secondary" onclick="closeModal('generic-status-modal')">${cancelText}</button>` : ''}
          <button class="btn btn-primary" id="status-modal-confirm-btn">${confirmText}</button>
        </div>
      </div>
    </div>
  `;

  openModal('generic-status-modal');

  const confirmBtn = document.getElementById('status-modal-confirm-btn');
  if (confirmBtn) {
    confirmBtn.onclick = () => {
      closeModal('generic-status-modal');
      if (typeof onConfirm === 'function') onConfirm();
    };
  }
}

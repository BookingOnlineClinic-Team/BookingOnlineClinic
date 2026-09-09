document.addEventListener('DOMContentLoaded', () => {
  const profileCards = document.querySelectorAll('.patient-profile-card');
  const continueBtn = document.getElementById('btn-continue-booking');
  const searchInput = document.getElementById('profile-search-input');
  const emptyState = document.getElementById('profile-empty-state');
  const profilesGrid = document.getElementById('profiles-grid');
  const searchClearBtn = document.getElementById('btn-search-clear');
  const selectedProfileInput = document.getElementById('selected-profile-id');
  const barSelectedName = document.getElementById('bar-selected-name');

  let selectedId = null;

  function updateContinueButton() {
    if (!continueBtn) return;
    const baseUrl = continueBtn.getAttribute('data-base-url');
    if (selectedId && baseUrl) {
      continueBtn.href = baseUrl + '?profile_id=' + encodeURIComponent(selectedId);
      continueBtn.classList.remove('disabled');
      continueBtn.removeAttribute('disabled');
    } else {
      continueBtn.href = '#';
      continueBtn.classList.add('disabled');
      continueBtn.setAttribute('disabled', 'true');
    }
  }

  function selectProfile(card) {
    profileCards.forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    selectedId = card.getAttribute('data-profile-id');

    if (selectedProfileInput) selectedProfileInput.value = selectedId;
    if (barSelectedName) {
      barSelectedName.textContent = card.querySelector('.patient-name')?.innerText || '';
    }
    updateContinueButton();
  }

  profileCards.forEach(card => {
    card.addEventListener('click', () => selectProfile(card));
  });

  const preSelected = document.querySelector('.patient-profile-card.selected');
  if (preSelected) {
    selectProfile(preSelected);
  } else {
    updateContinueButton();
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const keyword = searchInput.value.trim().toLowerCase();
      let matchCount = 0;

      if (searchClearBtn) {
        searchClearBtn.classList.toggle('visible', keyword.length > 0);
      }

      const allCards = document.querySelectorAll('.patient-profile-card');
      allCards.forEach(card => {
        const name = (card.getAttribute('data-name') || '').toLowerCase();
        const phone = (card.getAttribute('data-phone') || '').toLowerCase();

        if (!keyword || name.includes(keyword) || phone.includes(keyword)) {
          card.style.display = 'flex';
          matchCount++;
        } else {
          card.style.display = 'none';
        }
      });

      if (emptyState && profilesGrid && allCards.length > 0) {
        if (matchCount === 0) {
          emptyState.style.display = 'block';
          profilesGrid.style.display = 'none';
        } else {
          emptyState.style.display = 'none';
          profilesGrid.style.display = 'grid';
        }
      }
    });

    if (searchClearBtn) {
      searchClearBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input'));
        searchInput.focus();
      });
    }
  }
});

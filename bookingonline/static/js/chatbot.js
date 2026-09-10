/**
 * Chatbot
 * Điều khiển toàn bộ luồng: mở cửa sổ -> chọn ngày -> nhập triệu chứng ->
 * gọi API phân tích -> hiển thị chuyên khoa/bác sĩ/khung giờ -> điều hướng
 * sang màn hình đặt lịch (prefill).
 */
(function () {
  const cfg = window.CHATBOT_CONFIG;
  if (!cfg) return;

  const fab = document.getElementById("chatbot-fab");
  const panel = document.getElementById("chatbot-panel");
  const closeBtn = document.getElementById("chatbot-close-btn");
  const messagesEl = document.getElementById("chatbot-messages");
  const inputArea = document.getElementById("chatbot-input-area");
  const textInput = document.getElementById("chatbot-text-input");
  const sendBtn = document.getElementById("chatbot-send-btn");

  let state = {
    sessionId: null,
    selectedDate: null,
    step: "idle",
  };

  function resetConversation() {
    state = { sessionId: null, selectedDate: null, step: "idle" };
    messagesEl.innerHTML = "";
    setInputEnabled(false);
  }

  function setInputEnabled(enabled) {
    textInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
    textInput.placeholder = enabled
      ? "Mô tả triệu chứng của bạn..."
      : "Vui lòng chọn ngày khám trước...";
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addBotBubble(text) {
    const div = document.createElement("div");
    div.className = "chat-bubble bot";
    div.textContent = text;
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
  }

  function addErrorBubble(text) {
    const div = document.createElement("div");
    div.className = "chat-bubble error";
    div.textContent = text;
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
  }

  function addUserBubble(text) {
    const div = document.createElement("div");
    div.className = "chat-bubble user";
    div.textContent = text;
    messagesEl.appendChild(div);
    scrollToBottom();
  }

  function addTypingIndicator() {
    const div = document.createElement("div");
    div.className = "chat-typing";
    div.id = "chat-typing-indicator";
    div.innerHTML = "<span></span><span></span><span></span>";
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
  }

  function removeTypingIndicator() {
    const el = document.getElementById("chat-typing-indicator");
    if (el) el.remove();
  }

  function addDatePillsBubble(dates) {
    const wrap = document.createElement("div");
    wrap.className = "chat-date-pills";
    dates.forEach((d) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chat-date-pill";
      btn.textContent = `${d.label} ${d.label_date}`;
      btn.addEventListener("click", () => onDateSelected(d.iso, btn, wrap));
      wrap.appendChild(btn);
    });
    messagesEl.appendChild(wrap);
    scrollToBottom();
  }

  function onDateSelected(iso, btn, wrap) {
    wrap.querySelectorAll(".chat-date-pill").forEach((b) => b.classList.remove("selected"));
    btn.classList.add("selected");
    state.selectedDate = iso;
    state.step = "awaiting_symptom";
    addUserBubble(`Ngày khám: ${btn.textContent}`);
    addBotBubble("Bạn hãy mô tả triệu chứng bạn đang gặp phải nhé, càng chi tiết mình càng gợi ý chính xác hơn.");
    setInputEnabled(true);
    textInput.focus();
  }

  function addSpecializationListBubble(specializations) {
    const wrap = document.createElement("div");
    wrap.className = "chat-spec-list";
    specializations.forEach((s) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chat-spec-item";
      btn.textContent = s.name;
      btn.addEventListener("click", () => onManualSpecializationPicked(s));
      wrap.appendChild(btn);
    });
    messagesEl.appendChild(wrap);
    scrollToBottom();
  }

  function addDoctorCardsBubble(doctors) {
    const wrap = document.createElement("div");
    wrap.className = "chat-doctor-cards";
    doctors.forEach((doc) => {
      const card = document.createElement("div");
      card.className = "chat-doctor-card";

      const head = document.createElement("div");
      head.className = "chat-doctor-card-head";
      head.innerHTML = `
        <div>
          <div class="chat-doctor-name">${escapeHtml(doc.name)}</div>
          <div class="chat-doctor-meta">${doc.experience || 0} năm kinh nghiệm &middot; ${doc.rating.toFixed(1)}★ &middot; ${escapeHtml(doc.room || "")}</div>
        </div>
        <div class="chat-doctor-fee">${escapeHtml(doc.fee)}</div>
      `;
      card.appendChild(head);

      const slotsWrap = document.createElement("div");
      slotsWrap.className = "chat-doctor-slots";
      let chosenSlot = null;
      doc.slots.forEach((slot) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chat-slot-chip";
        chip.textContent = slot.time;
        chip.addEventListener("click", () => {
          slotsWrap.querySelectorAll(".chat-slot-chip").forEach((c) => c.classList.remove("selected"));
          chip.classList.add("selected");
          chosenSlot = slot;
          bookBtn.disabled = false;
        });
        slotsWrap.appendChild(chip);
      });
      card.appendChild(slotsWrap);

      const bookBtn = document.createElement("button");
      bookBtn.type = "button";
      bookBtn.className = "chat-book-now-btn";
      bookBtn.textContent = "Đặt lịch ngay";
      bookBtn.disabled = true;
      bookBtn.addEventListener("click", () => {
        const slot = chosenSlot || doc.slots[0];
        goToScheduleScreen(doc, slot);
      });
      card.appendChild(bookBtn);

      wrap.appendChild(card);
    });
    messagesEl.appendChild(wrap);
    scrollToBottom();
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  function goToScheduleScreen(doc, slot) {
    if (!cfg.profileId) {
      showToast("Bạn cần chọn hoặc tạo hồ sơ khám trước khi đặt lịch.", "warning");
      window.location.href = cfg.selectProfileUrl;
      return;
    }
    const params = new URLSearchParams({
      profile_id: cfg.profileId,
      doctor_id: doc.doctor_id,
      pending_slot_value: `${slot.work_schedule_id}|${slot.time}`,
      pending_date: state.selectedDate,
      pending_reason: state.lastSymptomText || "",
      chatbot_suggestion_id: doc.suggestion_id || "",
    });
    window.location.href = `${cfg.scheduleUrl}?${params.toString()}`;
  }

  function onManualSpecializationPicked(spec) {
    addUserBubble(`Chọn chuyên khoa: ${spec.name}`);
    addTypingIndicator();
    fetch(cfg.manualSpecializationUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        specialization_id: spec.id,
        date: state.selectedDate,
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        removeTypingIndicator();
        handleSuggestionResult(data);
      })
      .catch(() => {
        removeTypingIndicator();
        showAiErrorFallback();
      });
  }

  function handleSuggestionResult(data) {
    if (data.session_id) state.sessionId = data.session_id;

    if (data.status === "NO_SLOTS") {
      addBotBubble(data.message);
      addBotBubble("Bạn vui lòng chọn một ngày khám khác:");
      fetchDatesAndRender();
      state.step = "pick_date";
      setInputEnabled(false);
      return;
    }

    if (data.status === "OK") {
      const confidenceNote = data.confidence === "LOW"
        ? " (mức độ chắc chắn chưa cao, bạn có thể chọn lại chuyên khoa khác nếu chưa phù hợp)"
        : "";
      addBotBubble(
        `Dựa trên mô tả của bạn, mình gợi ý chuyên khoa "${data.specialization.name}"${confidenceNote}.\n` +
        (data.reason ? `Lý do: ${data.reason}\n` : "") +
        "Danh sách bác sĩ và khung giờ trống còn lại:"
      );
      addDoctorCardsBubble(data.doctors);
      state.step = "awaiting_choice";
      setInputEnabled(false);
      return;
    }
  }

  function showAiErrorFallback(fallbackUrl) {
    const bubble = addErrorBubble(
      "Hệ thống gặp lỗi khi phân tích triệu chứng hoặc truy vấn dữ liệu, vui lòng thử lại sau."
    );
    if (fallbackUrl) {
      const link = document.createElement("a");
      link.href = fallbackUrl;
      link.textContent = "Chuyển đến trang Tìm kiếm bác sĩ";
      link.style.display = "inline-block";
      link.style.marginTop = "6px";
      link.style.fontWeight = "600";
      bubble.appendChild(document.createElement("br"));
      bubble.appendChild(link);
    }
  }

  function fetchDatesAndRender() {
    fetch(cfg.initUrl)
      .then((r) => r.json())
      .then((data) => addDatePillsBubble(data.dates))
      .catch(() => addErrorBubble("Không tải được danh sách ngày khám, vui lòng thử lại."));
  }

  function sendSymptomMessage(text) {
    addUserBubble(text);
    state.lastSymptomText = text;
    setInputEnabled(false);
    addTypingIndicator();

    fetch(cfg.analyzeUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        date: state.selectedDate,
        session_id: state.sessionId,
      }),
    })
      .then(async (r) => {
        const data = await r.json();
        return { ok: r.ok, data };
      })
      .then(({ ok, data }) => {
        removeTypingIndicator();
        if (!ok) {
          showAiErrorFallback(data.fallback_url);
          return;
        }
        if (data.session_id) state.sessionId = data.session_id;

        if (data.status === "NEED_MANUAL_SPECIALIZATION") {
          addBotBubble(data.message);
          addSpecializationListBubble(data.specializations);
          state.step = "awaiting_choice";
          return;
        }
        handleSuggestionResult(data);
      })
      .catch(() => {
        removeTypingIndicator();
        showAiErrorFallback();
      });
  }

  function openPanel() {
    panel.hidden = false;
    fab.classList.add("is-open");
    if (state.step === "idle") {
      addTypingIndicator();
      fetch(cfg.initUrl)
        .then((r) => r.json())
        .then((data) => {
          removeTypingIndicator();
          addBotBubble(data.greeting);
          addDatePillsBubble(data.dates);
          state.step = "pick_date";
        })
        .catch(() => {
          removeTypingIndicator();
          addErrorBubble("Không thể kết nối Chatbot, vui lòng thử lại sau.");
        });
    }
  }

  function closePanel() {
    panel.hidden = true;
    fab.classList.remove("is-open");
    resetConversation();
  }

  fab.addEventListener("click", openPanel);
  closeBtn.addEventListener("click", closePanel);
   // Nối các điểm chạm Chatbot đã có sẵn trong giao diện (menu điều hướng
  // và bong bóng preview ở trang chủ) vào cùng một hàm mở panel thật.
  const navChatbotBtn = document.getElementById("nav-chatbot");
  if (navChatbotBtn) {
    navChatbotBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openPanel();
    });
  }

  const previewBubble = document.getElementById("chatbot-preview-bubble");
  if (previewBubble) {
    previewBubble.addEventListener("click", openPanel);
  }
  sendBtn.addEventListener("click", () => {
    const text = textInput.value.trim();
    if (!text || state.step !== "awaiting_symptom") return;
    textInput.value = "";
    sendSymptomMessage(text);
  });

  textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendBtn.click();
    }
  });

  setInputEnabled(false);
})();
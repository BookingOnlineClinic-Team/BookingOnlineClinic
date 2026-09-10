import json
import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

SYSTEM_INSTRUCTION = """Bạn là trợ lý y tế của một phòng khám đa khoa.
                        Nhiệm vụ: đọc mô tả triệu chứng của bệnh nhân (tiếng Việt, ngôn ngữ tự nhiên,
                        có thể viết tắt/không dấu) và chọn ĐÚNG MỘT chuyên khoa phù hợp nhất trong
                        danh sách chuyên khoa được cung cấp.
                        
                        Quy tắc bắt buộc:
                        - CHỈ được chọn specialization_id có trong danh sách được cung cấp, không
                          được tự bịa ra chuyên khoa mới.
                        - Nếu mô tả quá mơ hồ, quá ngắn (vd: "chào", "test"), không liên quan y tế,
                          hoặc không đủ căn cứ để xác định chuyên khoa thì trả specialization_id = null.
                        - Không chẩn đoán bệnh, không kê đơn, không tư vấn điều trị. Chỉ định hướng
                          chuyên khoa để đặt lịch khám.
                        - Trả lời NGẮN GỌN, đúng định dạng JSON yêu cầu, không thêm chữ nào khác.
                    """

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "specialization_id": {
            "type": "INTEGER",
            "nullable": True,
            "description": "id chuyên khoa được chọn từ danh sách, hoặc null nếu không xác định được",
        },
        "confidence": {
            "type": "STRING",
            "enum": ["HIGH", "MEDIUM", "LOW"],
        },
        "reason": {
            "type": "STRING",
            "description": "Giải thích ngắn gọn (1-2 câu, tiếng Việt) vì sao chọn chuyên khoa này",
        },
    },
    "required": ["specialization_id", "confidence", "reason"],
}


class GeminiServiceError(Exception):
    """Lỗi khi gọi Gemini API hoặc parse kết quả (ánh xạ vào luồng ngoại lệ UC_03)."""


def classify_specialization(symptom_text: str, specializations: list[dict]) -> dict:
    if not GEMINI_API_KEY:
        raise GeminiServiceError("Thiếu cấu hình GEMINI_API_KEY trong biến môi trường.")

    specialization_catalog = "\n".join(
        f"- id={s['id']}, tên=\"{s['name']}\", mô tả=\"{s['description']}\""
        for s in specializations
    )

    user_prompt = (
        f"DANH SÁCH CHUYÊN KHOA HIỆN CÓ CỦA PHÒNG KHÁM:\n{specialization_catalog}\n\n"
        f"MÔ TẢ TRIỆU CHỨNG CỦA BỆNH NHÂN:\n\"{symptom_text}\"\n\n"
        f"Hãy chọn specialization_id phù hợp nhất theo đúng JSON schema."
    )

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": _RESPONSE_SCHEMA,
        },
    }

    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(raw_text)
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise GeminiServiceError(f"Gemini API lỗi hoặc trả về dữ liệu không hợp lệ: {exc}") from exc

    valid_ids = {s["id"] for s in specializations}
    spec_id = result.get("specialization_id")
    if spec_id is not None and spec_id not in valid_ids:
        # Gemini ra id không tồn tại -> coi như không xác định được,
        # để hệ thống rơi vào luồng thay thế (chọn thủ công) thay vì báo sai bác sĩ.
        spec_id = None

    return {
        "specialization_id": spec_id,
        "confidence": result.get("confidence", "LOW"),
        "reason": result.get("reason", ""),
    }
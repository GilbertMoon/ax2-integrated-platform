# ============================================================
# face-recognition-service/app.py
# 얼굴인식 전용 API 서버. Django(포트 8000)와는 별개로,
# 이 서버는 포트 5001에서 실행합니다.
# ============================================================

import os
import tempfile
import traceback
import uuid

from deepface import DeepFace
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 로컬 HTML 파일(file://)에서 이 서버를 호출할 수 있게 허용

# 이 거리값보다 작으면 "같은 사람"으로 판정 (Facenet 모델 기준 권장값)
MATCH_THRESHOLD = 0.4


def _save_upload_to_temp(uploaded_file) -> str:
    """
    업로드된 파일을 임시 폴더에 저장하고 경로를 반환한다.
    (Windows에서 NamedTemporaryFile을 쓰면 파일 잠금 문제가 생겨서,
     단순히 경로만 만들고 save()로 바로 쓰는 방식으로 변경)
    """
    ext = os.path.splitext(uploaded_file.filename or "")[1] or ".jpg"
    temp_path = os.path.join(tempfile.gettempdir(), f"face_{uuid.uuid4().hex}{ext}")
    uploaded_file.save(temp_path)
    return temp_path


def _safe_delete(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass  # 삭제 실패해도 서비스 동작에는 지장 없음, 그냥 넘어감


def _describe_error(error: Exception) -> str:
    """
    DeepFace는 내부 에러를 ValueError로 감싸서 다시 던지는 경우가 많다
    (raise ValueError(...) from original_error).
    이 함수는 그 안쪽에 숨어있는 "진짜 원인"까지 따라가서 전부 보여준다.
    """
    parts = []
    current = error
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        parts.append(f"{type(current).__name__}: {current}")
        current = current.__cause__ or current.__context__
    return " <- 원인: ".join(parts)


@app.route("/embed/", methods=["POST"])
def embed():
    """
    사진 하나를 받아서 "얼굴 특징 벡터(임베딩)"를 계산해 반환합니다.
    이 벡터는 숫자 목록(보통 128개)이고, 나중에 비교할 때
    DeepFace를 다시 부르지 않고도 빠르게 거리 계산이 가능합니다.

    호출 예 (multipart/form-data):
      image: 사진 파일
      check_liveness: "true"면 실제 사람인지(사진/화면 재촬영이 아닌지) 먼저 확인합니다.
                       (등록용 정적 프로필 사진에는 "false", 실시간 촬영 사진에는 "true" 권장)

    응답 예: {"embedding": [0.123, -0.045, ...]}
    라이브니스 실패 시 (403): {"error": "spoof_detected", "message": "..."}
    """
    image_file = request.files.get("image")
    if image_file is None:
        return jsonify({"error": "image 파일이 필요합니다."}), 400

    check_liveness = request.form.get("check_liveness", "false").lower() == "true"
    image_path = _save_upload_to_temp(image_file)

    try:
        if check_liveness:
            # 사진/화면 재촬영(스푸핑)인지 먼저 확인한다.
            # 처음 실행 시 위조 방지용 AI 모델을 추가로 다운로드합니다 (최초 1회만, 시간이 좀 걸림).
            faces = DeepFace.extract_faces(
                img_path=image_path,
                anti_spoofing=True,
                enforce_detection=False,
            )
            if not faces:
                return jsonify({"error": "얼굴을 찾을 수 없습니다."}), 400

            face = faces[0]
            is_real = face.get("is_real", True)
            antispoof_score = face.get("antispoof_score")

            if not is_real:
                return jsonify({
                    "error": "spoof_detected",
                    "message": "실제 사람이 아닌 것으로 판단되었습니다. 사진이나 화면이 아닌 실제 얼굴로 다시 촬영해주세요.",
                    "antispoof_score": antispoof_score,
                }), 403

        result = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet",
            enforce_detection=False,
        )
        # represent()는 리스트를 반환 (사진에 얼굴이 여러 개일 수 있어서). 첫 번째 얼굴만 사용.
        embedding = result[0]["embedding"]
        return jsonify({"embedding": embedding})
    except Exception as error:
        return jsonify({"error": _describe_error(error)}), 500
    finally:
        _safe_delete(image_path)


@app.route("/health/", methods=["GET"])
def health():
    """서버가 살아있는지 확인용."""
    return jsonify({"status": "ok"})


@app.route("/compare/", methods=["POST"])
def compare():
    """
    두 사진을 받아서 같은 사람인지 비교합니다.

    호출 예 (multipart/form-data):
      image1: 방금 촬영한 사진
      image2: 비교 대상(예: 학생 프로필 사진)

    응답 예:
      {"same_person": true, "distance": 0.28}
    """
    image1 = request.files.get("image1")
    image2 = request.files.get("image2")
    if image1 is None or image2 is None:
        return jsonify({"error": "image1, image2 두 파일이 모두 필요합니다."}), 400

    path1 = _save_upload_to_temp(image1)
    path2 = _save_upload_to_temp(image2)

    try:
        result = DeepFace.verify(
            img1_path=path1,
            img2_path=path2,
            model_name="Facenet",
            enforce_detection=False,
        )
        return jsonify({
            "same_person": result["distance"] <= MATCH_THRESHOLD,
            "distance": result["distance"],
        })
    except Exception as error:
        # [임시 디버깅용] 원인 파악 후 다시 간단한 메시지로 되돌릴 예정
        return jsonify({
            "error": _describe_error(error),
            "traceback": traceback.format_exc(),
        }), 500
    finally:
        _safe_delete(path1)
        _safe_delete(path2)


@app.route("/find-match/", methods=["POST"])
def find_match():
    """
    촬영한 사진 하나와, 후보 여러 명의 사진을 한 번에 비교해서
    가장 닮은 사람을 찾습니다.

    호출 예 (multipart/form-data):
      captured: 방금 촬영한 사진
      candidate_0: 후보1 사진, candidate_0_id: 후보1의 user_id
      candidate_1: 후보2 사진, candidate_1_id: 후보2의 user_id
      ... (개수만큼 반복)

    응답 예:
      {"matched": true, "user_id": "7", "distance": 0.31}
      또는
      {"matched": false, "best_distance": 0.55}
    """
    captured = request.files.get("captured")
    if captured is None:
        return jsonify({"error": "captured 파일이 필요합니다."}), 400

    captured_path = _save_upload_to_temp(captured)

    best_user_id = None
    best_distance = None
    temp_paths_to_clean = [captured_path]

    try:
        index = 0
        while f"candidate_{index}" in request.files:
            candidate_file = request.files[f"candidate_{index}"]
            candidate_id = request.form.get(f"candidate_{index}_id")

            candidate_path = _save_upload_to_temp(candidate_file)
            temp_paths_to_clean.append(candidate_path)

            try:
                result = DeepFace.verify(
                    img1_path=captured_path,
                    img2_path=candidate_path,
                    model_name="Facenet",
                    enforce_detection=False,
                )
                distance = result["distance"]
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_user_id = candidate_id
            except Exception:
                pass  # 이 후보 비교 실패해도 나머지는 계속 진행

            index += 1

        if best_distance is not None and best_distance <= MATCH_THRESHOLD:
            return jsonify({"matched": True, "user_id": best_user_id, "distance": best_distance})
        return jsonify({"matched": False, "best_distance": best_distance})
    finally:
        for path in temp_paths_to_clean:
            _safe_delete(path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
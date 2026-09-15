(() => {
  const input = document.getElementById("id_screenshot");
  if (!input) return;
  const preview = document.getElementById("capture-preview");
  const image = document.getElementById("capture-image");
  const message = document.getElementById("capture-message");
  let objectUrl;
  function updatePreview() {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    preview.hidden = true;
    message.textContent = "";
    const file = input.files[0];
    if (!file) return;
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 5 * 1024 * 1024) {
      message.textContent = "5MB 이하의 PNG, JPG, WebP 이미지를 선택해 주세요.";
      input.value = "";
      return;
    }
    objectUrl = URL.createObjectURL(file);
    image.src = objectUrl;
    preview.hidden = false;
  }
  input.addEventListener("change", updatePreview);
  document.getElementById("remove-capture").addEventListener("click", () => {
    input.value = "";
    updatePreview();
  });
  document.addEventListener("paste", event => {
    const file = Array.from(event.clipboardData?.files || []).find(file => file.type.startsWith("image/"));
    if (!file) return;
    event.preventDefault();
    const data = new DataTransfer();
    data.items.add(file);
    input.files = data.files;
    updatePreview();
  });
})();

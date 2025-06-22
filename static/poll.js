function pollForResponse(id) {
  const t = document.getElementById('response-text');
  (function check() {
    fetch(`/check_update/${id}`)
      .then(r => r.json())
      .then(data => {
        if (data.response) t.textContent = data.response;
        else setTimeout(check, 2000);
      })
      .catch(() => setTimeout(check, 5000));
  })();
}

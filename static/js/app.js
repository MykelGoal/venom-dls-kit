// ===== VENOM DLS frontend logic =====

// Live kit designer
const genBtn = document.getElementById('d-generate');
if (genBtn) {
  genBtn.addEventListener('click', async () => {
    const body = {
      primary: document.getElementById('d-primary').value,
      secondary: document.getElementById('d-secondary').value,
      socks: document.getElementById('d-socks').value,
      style: document.getElementById('d-style').value,
      club: 'custom'
    };
    genBtn.textContent = 'Building...';
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const j = await res.json();
      const full = location.origin + j.url;
      document.getElementById('d-img').src = full;
      document.getElementById('d-url').value = full;
      document.getElementById('d-result').style.display = 'block';
    } catch (e) {}
    genBtn.textContent = 'Generate my kit';
  });
}

// Copy-link buttons (designer + featured kits)
document.querySelectorAll('.copy-btn').forEach(b => {
  b.addEventListener('click', async () => {
    const inp = b.parentElement.querySelector('input');
    if (!inp) return;
    try {
      await navigator.clipboard.writeText(inp.value);
      b.textContent = 'Copied!';
      setTimeout(() => (b.textContent = 'Copy'), 1500);
    } catch (e) {}
  });
});

// Order form -> backend
const form = document.getElementById('orderForm');
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      await res.json();
      document.getElementById('orderStatus').textContent = 'Order received! We\'ll reach out on WhatsApp. 🐍';
      form.reset();
    } catch (e) {
      document.getElementById('orderStatus').textContent = 'Something went wrong — please use WhatsApp instead.';
    }
  });
}

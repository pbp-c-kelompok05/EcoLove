(() => {
  'use strict';
  const root = document.querySelector('.ee');
  if (!root) return;
  const feedback = document.querySelector('#ee-feedback');
  function message(text, error = false) {
    feedback.textContent = text;
    feedback.classList.toggle('ee-error', error);
  }
  async function send(url, options = {}) {
    const response = await fetch(url, {...options, headers: {'X-Requested-With': 'XMLHttpRequest', ...options.headers}});
    let data;
    try { data = await response.json(); } catch { throw new Error('Respons server tidak dapat dibaca. Muat ulang halaman dan coba lagi.'); }
    if (!response.ok) {
      const error = new Error(data.error || 'Permintaan gagal. Periksa isian atau login kembali.');
      error.fields = data.errors;
      throw error;
    }
    return data;
  }
  // HTML hanya berasal dari partial template Django yang melakukan autoescape.
  function fragment(html) {
    return new DOMParser().parseFromString(html, 'text/html').body;
  }
  function errors(form, error) {
    form.querySelectorAll('[data-errors-for], .ee-errors').forEach(el => el.replaceChildren());
    form.querySelectorAll('[aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
    const summary = form.querySelector('.ee-errors');
    if (summary) summary.textContent = error.message;
    for (const [name, values] of Object.entries(error.fields || {})) {
      const holder = Array.from(form.querySelectorAll('[data-errors-for]')).find(el => el.dataset.errorsFor === name) || summary;
      if (holder) holder.textContent += ' ' + values.map(v => v.message).join(' ');
      const input = form.elements.namedItem(name);
      if (input) input.setAttribute('aria-invalid', 'true');
    }
    if (summary) summary.focus();
    message(error.message, true);
  }
  const filter = document.querySelector('#ee-filter');
  if (filter) {
    let controller, timer;
    const results = document.querySelector('#ee-results');
    async function load(page = 1) {
      controller?.abort();
      controller = new AbortController();
      const current = controller;
      const params = new URLSearchParams(new FormData(filter));
      params.set('page', page);
      message('Memuat hasil…');
      results.setAttribute('aria-busy', 'true');
      try {
        const data = await send(filter.action + '?' + params, {signal: current.signal});
        results.replaceChildren(...fragment(data.html).childNodes);
        history.replaceState(null, '', filter.action + '?' + params);
        message('Hasil diperbarui.');
      } catch (e) { if (e.name !== 'AbortError') message('Gagal memuat hasil. Klik Terapkan untuk mencoba lagi. ' + e.message, true); }
      finally { if (!current.signal.aborted) results.removeAttribute('aria-busy'); }
    }
    filter.addEventListener('submit', e => { e.preventDefault(); clearTimeout(timer); load(); });
    filter.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => load(), 350); });
    results.addEventListener('click', e => {
      const link = e.target.closest('[data-page]');
      if (link) { e.preventDefault(); clearTimeout(timer); load(link.dataset.page); }
    });
  }
  root.addEventListener('submit', async e => {
    const form = e.target;
    if (!form.matches('#ee-content-form, #ee-comment-form, [data-delete]')) return;
    e.preventDefault();
    if (form.hasAttribute('data-delete') && !confirm('Hapus data ini? Tindakan ini tidak dapat dibatalkan.')) return;
    const button = form.querySelector('[type=submit]');
    if (button.disabled) return;
    button.disabled = true;
    message('Menyimpan perubahan…');
    try {
      const data = await send(form.action || location.href, {method:'POST', body:new FormData(form)});
      if (data.url) { location.assign(data.url); return; }
      if (form.id === 'ee-comment-form') {
        document.querySelector('#ee-comments').append(...fragment(data.html).childNodes);
        form.reset();
        form.querySelector('.ee-errors').replaceChildren();
      } else { form.closest('.ee-comment').remove(); }
      const empty = document.querySelector('#ee-comments-empty');
      if (empty) empty.hidden = !!document.querySelector('.ee-comment');
      message('Perubahan berhasil disimpan.');
    } catch (error) { errors(form, error); }
    finally { button.disabled = false; }
  });
})();

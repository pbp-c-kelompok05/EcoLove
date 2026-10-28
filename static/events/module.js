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
  function clearErrors(form) {
    form.querySelectorAll('[data-errors-for], .ee-errors').forEach(el => el.replaceChildren());
    form.querySelectorAll('[aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
  }
  function errors(form, error) {
    clearErrors(form);
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
    function cancelPending() {
      clearTimeout(timer);
      controller?.abort();
      results.removeAttribute('aria-busy');
    }
    async function load(page = 1, remember = true) {
      controller?.abort();
      controller = new AbortController();
      const current = controller;
      const params = new URLSearchParams(new FormData(filter));
      params.set('page', page);
      message('Memuat hasil…');
      results.setAttribute('aria-busy', 'true');
      try {
        const data = await send(filter.action + '?' + params, {signal: current.signal});
        if (current.signal.aborted) return;
        results.replaceChildren(...fragment(data.html).childNodes);
        params.set('page', data.page);
        const url = new URL(filter.action + '?' + params);
        if (remember && url.href !== location.href) history.pushState(null, '', url);
        message('Hasil diperbarui.');
      } catch (e) { if (e.name !== 'AbortError') message('Gagal memuat hasil. Klik Cari untuk mencoba lagi. ' + e.message, true); }
      finally { if (!current.signal.aborted) results.removeAttribute('aria-busy'); }
    }
    filter.addEventListener('submit', e => { e.preventDefault(); cancelPending(); load(); });
    filter.addEventListener('input', () => { cancelPending(); timer = setTimeout(() => load(), 350); });
    results.addEventListener('click', e => {
      const link = e.target.closest('[data-page]');
      if (link && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey && e.button === 0) {
        e.preventDefault(); cancelPending(); load(link.dataset.page);
      }
    });
    window.addEventListener('popstate', () => {
      cancelPending();
      const params = new URLSearchParams(location.search);
      if (filter.dataset.kind === 'event' && params.get('category') === 'community') {
        params.delete('category');
        const url = new URL(location.href);
        url.search = params.toString();
        history.replaceState(null, '', url);
      }
      for (const name of ['q', 'category', 'status']) {
        const input = filter.elements.namedItem(name);
        if (input) input.value = params.get(name) || '';
      }
      load(params.get('page') || 1, false);
    });
  }
  const commentForm = document.querySelector('#ee-comment-form');
  if (commentForm) {
    const imageInput = commentForm.querySelector('input[name=image]');
    const preview = document.querySelector('#ee-comment-preview');
    const previewImage = preview.querySelector('img');
    let previewUrl;
    function clearPreview() {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrl = null;
      previewImage.removeAttribute('src');
      preview.hidden = true;
    }
    imageInput.addEventListener('change', () => {
      clearPreview();
      const file = imageInput.files[0];
      if (!file || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return;
      previewUrl = URL.createObjectURL(file);
      previewImage.src = previewUrl;
      preview.hidden = false;
    });
    previewImage.addEventListener('error', () => { preview.hidden = true; });
    document.querySelector('#ee-remove-comment-image').addEventListener('click', () => {
      imageInput.value = '';
      clearPreview();
    });
    commentForm.addEventListener('reset', clearPreview);
    window.addEventListener('pagehide', clearPreview);
  }
  root.addEventListener('submit', async e => {
    const form = e.target;
    if (!form.matches('#ee-content-form, #ee-comment-form, #ee-delete-confirm-form, [data-delete], [data-participation]')) return;
    e.preventDefault();
    if (form.hasAttribute('data-delete') && !confirm('Hapus data ini? Tindakan ini tidak dapat dibatalkan.')) return;
    const button = form.querySelector('[type=submit]');
    if (button.disabled) return;
    button.disabled = true;
    form.setAttribute('aria-busy', 'true');
    const originalLabel = button.textContent;
    button.textContent = form.matches('[data-delete], #ee-delete-confirm-form') ? 'Menghapus…' : 'Menyimpan…';
    message('Menyimpan perubahan…');
    try {
      // A field named "action" shadows form.action on HTMLFormElement.
      const data = await send(form.getAttribute('action') || location.href, {method:'POST', body:new FormData(form)});
      if (data.url) { location.assign(data.url); return; }
      if (form.id === 'ee-comment-form') {
        document.querySelector('#ee-comments').append(...fragment(data.html).childNodes);
        form.reset();
        clearErrors(form);
      } else { form.closest('.ee-comment').remove(); }
      const empty = document.querySelector('#ee-comments-empty');
      if (empty) empty.hidden = !!document.querySelector('.ee-comment');
      message('Perubahan berhasil disimpan.');
    } catch (error) { errors(form, error); }
    finally {
      button.disabled = false;
      button.textContent = originalLabel;
      form.removeAttribute('aria-busy');
    }
  });
})();

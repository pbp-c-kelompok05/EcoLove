const buyBtn = document.getElementById('buy-button');

if (buyBtn) {
  buyBtn.addEventListener('click', async () => {
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
    buyBtn.disabled = true;

    try {
      const res = await fetch(buyBtn.dataset.url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf },
      });
      const data = await res.json();
      if (!res.ok) { alert(data.message); return; }

      window.snap.pay(data.token, {
        onSuccess: async () => {
          await fetch(`/marketplace/pay/status/${data.order_id}/`);
          alert('Payment successful!');
          location.reload();
        },
        onPending: () => { alert('Waiting for your payment.'); },
        onError:   () => { alert('Payment failed.'); },
        onClose:   () => { /* user closed popup */ },
      });
    } finally {
      buyBtn.disabled = false;
    }
  });
}
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

      const syncStatus = () => fetch(`/payments/pay/status/${data.order_id}/`);

      window.snap.pay(data.token, {
        onSuccess: async () => {
          await syncStatus();
          alert('Payment successful!');
          location.reload();
        },
        onPending: async () => {
          await syncStatus();
          alert('Waiting for your payment.');
          location.reload();
        },
        onError: async () => {
          await syncStatus();
          alert('Payment failed.');
          location.reload();
        },
        onClose: () => {
          // popup closed without finishing: reload so the page shows "Resume payment" and "Cancel payment"
          location.reload();
        },
      });
    } finally {
      buyBtn.disabled = false;
    }
  });
}
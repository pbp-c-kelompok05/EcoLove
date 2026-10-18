// Endpoint and Configs
const GRID = document.querySelector('#grid');

const GET_ITEMS_ENDPOINT = GRID.dataset.getItemsJson;
const ITEM_DETAIL_ENDPOINT = GRID.dataset.itemDetail;
const LIKE_ITEM_ENDPOINT = GRID.dataset.likeItem;
const DISLIKE_ITEM_ENDPOINT = GRID.dataset.dislikeItem;
const IS_AUTHENTICATED = GRID.dataset.isAuthenticated === 'True';
const USER_ID = GRID.dataset.userId;
let productsAbortController;

// DOM Elements
const loadingState = document.getElementById('loading');
const errorState = document.getElementById('error');
const emptyState = document.getElementById('empty');
const gridContainer = document.getElementById('grid');

function displayPageSection({ showLoading = false, showError = false, showEmpty = false, showGrid = false }) {
    loadingState.classList.toggle('hide', !showLoading);
    errorState.classList.toggle('hide', !showError);
    emptyState.classList.toggle('hide', !showEmpty);
    gridContainer.classList.toggle('hide', !showGrid);
}

function buildProductCard(item) {
    const productId = item.pk;
    const product = item.fields;

    const card = document.createElement('article');
    card.setAttribute('class', 'product-card');
    card.setAttribute('style', 'display: flex; flex-direction: column; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; height: 100%;');

    // Menggunakan variabel detailUrl resmi dari JavaScript
    const detailUrl = ITEM_DETAIL_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', productId);

    // Placeholder jika gambar kosong agar area atas tetap rapi dan bisa diklik
    const image = product.image
        ? `<img class="product-image" src="${product.image}" style="height: 200px; width: 100%; object-fit: cover;">`
        : `<div class="product-image" style="height: 200px; width: 100%; background-color: #f0fdf4; display: flex; align-items: center; justify-content: center; color: #2e7d32; font-weight: 600;">No Image Available</div>`;

    const cardContent = `
        <a href="${detailUrl}" style="text-decoration: none; color: inherit; display: block;">
            ${image}
        </a>
        <div class="card-content" style="padding: 16px; display: flex; flex-direction: column; flex-grow: 1; justify-content: space-between;">
            <div>
                <span class="tag">${product.category}</span>

                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; gap: 8px;">
                    <!-- Perbaikan Link 404: Menggunakan ${detailUrl} bukan Django tag -->
                    <a href="${detailUrl}" style="text-decoration: none; color: inherit; flex-grow: 1;">
                        <h3 style="margin: 0; font-size: 1.1rem;">${product.name}</h3>
                    </a>
                </div>
            </div>

            <p style="margin-top: 12px; font-weight: 600;">\$${product.price}</p>
        </div>
    `;

    card.innerHTML = cardContent;

    if (IS_AUTHENTICATED) {
        const targetDiv = card.querySelector('.card-content > div > div');
        if (targetDiv) {
            targetDiv.appendChild(buildProductActions(item));
        }
    }

    return card;
}

function buildProductActions(item) {
    const product = item.fields;

    const productActions = document.createElement('div');
    productActions.setAttribute('class', 'interaction-buttons');
    productActions.setAttribute('style', 'display: flex; gap: 6px; flex-shrink: 0;');

    const likeButton = document.createElement('button');
    likeButton.innerHTML = `👍 ${product.like_count}`;
    likeButton.classList.toggle('liked', product.is_liked);

    likeButton.addEventListener('click', async function (event) {
        event.preventDefault();
        event.stopPropagation(); // Mencegah klik terobosan ke link kartu
        await like(item);

        likeButton.innerHTML = `👍 ${product.like_count}`;
        likeButton.classList.toggle('liked', product.is_liked);
        dislikeButton.innerHTML = `👎 ${product.dislike_count}`;
        dislikeButton.classList.toggle('disliked', product.is_disliked);
    });

    const dislikeButton = document.createElement('button');
    dislikeButton.innerHTML = `👎 ${product.dislike_count}`;
    dislikeButton.classList.toggle('disliked', product.is_disliked);

    dislikeButton.addEventListener('click', async function (event) {
        event.preventDefault();
        event.stopPropagation(); // Mencegah klik terobosan ke link kartu
        await dislike(item);

        likeButton.innerHTML = `👍 ${product.like_count}`;
        likeButton.classList.toggle('liked', product.is_liked);
        dislikeButton.innerHTML = `👎 ${product.dislike_count}`;
        dislikeButton.classList.toggle('disliked', product.is_disliked);
    });

    if (USER_ID === item.user_id) {
        likeButton.disabled = true;
        dislikeButton.disabled = true;
    }

    productActions.appendChild(likeButton);
    productActions.appendChild(dislikeButton);

    return productActions;
}

async function like(item) {
    const product = item.fields;
    const likeUrl = LIKE_ITEM_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

    try {
        const response = await fetch(likeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        if (response.ok) {
            product.like_count = result.like_count;
            product.is_liked = result.is_liked;
            product.dislike_count = result.dislike_count;
            product.is_disliked = result.is_disliked;
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ITEM ERROR:', error);
    }
}

async function dislike(item) {
    const product = item.fields;
    const dislikeUrl = DISLIKE_ITEM_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

    try {
        const response = await fetch(dislikeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        if (response.ok) {
            product.like_count = result.like_count;
            product.is_liked = result.is_liked;
            product.dislike_count = result.dislike_count;
            product.is_disliked = result.is_disliked;
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ITEM ERROR:', error);
    }
}

async function fetchProducts(searchQuery = "") {
    if (productsAbortController) productsAbortController.abort();
    productsAbortController = new AbortController();

    try {
        displayPageSection({ showLoading: true });

        const url = searchQuery ? `${GET_ITEMS_ENDPOINT}?title=${encodeURIComponent(searchQuery)}` : GET_ITEMS_ENDPOINT;

        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: productsAbortController.signal,
        });

        if (!response.ok) throw new Error('Failed to fetch data');

        const productsData = await response.json();

        if (productsData.length === 0) {
            displayPageSection({ showEmpty: true });
        } else {
            gridContainer.innerHTML = '';
            productsData.forEach(item => {
                gridContainer.appendChild(buildProductCard(item));
            });
            displayPageSection({ showGrid: true });
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('ITEM ERROR:', error);
        displayPageSection({ showError: true });
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    if (!cookieValue) {
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) cookieValue = csrfInput.value;
    }
    return cookieValue;
}

fetchProducts();
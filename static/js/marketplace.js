// Endpoint and Configs
const GRID = document.querySelector('#grid');

const GET_ITEMS_ENDPOINT = GRID.dataset.getItemsJson;
const ITEM_DETAIL_ENDPOINT = GRID.dataset.itemDetail;
const LIKE_ITEM_ENDPOINT = GRID.dataset.likeItem;
const DISLIKE_ITEM_ENDPOINT = GRID.dataset.dislikeItem;
const IS_AUTHENTICATED= GRID.dataset.isAuthenticated === 'True';
let productsAbortController;

// DOM Elements
const loadingState = document.getElementById('loading');
const errorState = document.getElementById('error');
const emptyState = document.getElementById('empty');
const gridContainer = document.getElementById('grid');

function displayPageSection({ showLoading=false, showError=false, showEmpty=false, showGrid=false }) {
    loadingState.classList.toggle('hide', !showLoading);
    errorState.classList.toggle('hide', !showError);
    emptyState.classList.toggle('hide', !showEmpty);
    gridContainer.classList.toggle('hide', !showGrid);
}

function buildProductCard(item) {
    const productId = item.pk;
    const product = item.fields;

    // Product's Card
    const card = document.createElement('article');
    card.setAttribute('class', 'product-card')

    // Product's URLs
    const detailUrl = ITEM_DETAIL_ENDPOINT.replace('0', productId);
    
    // Product's Image
    const image = product.image
        ? `<img class="product-image" src="${product.image}" style="height: 200px; width: 100%; object-fit: cover;">`
        : '<img class="product-image" style="background-color: #a3d9a5; height: 200px;">';

    const cardContent = `
        <a href="${detailUrl}">${image}</a>
        <div class="card-content">
            <span class="tag">${product.category}</span>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                <a href="{% url 'items:item_detail' item.id %}" style="text-decoration: none; color: inherit;">
                    <h3 style="margin: 0; font-size: 1.1rem;">${product.name}</h3>
                </a>

            </div>

            <p style="margin-top: 8px; font-weight: 600;">Rp${product.price}</p>
        </div>
    `;

    card.innerHTML = cardContent;
    if (IS_AUTHENTICATED) card.getElementsByTagName('div').item(0)
        .getElementsByTagName('div').item(0).appendChild(buildProductActions(item));
    return card;
}

function buildProductActions(item) {
    const product = item.fields;

    const productActions = document.createElement('div');
    productActions.setAttribute('class', 'interaction-buttons');
    productActions.setAttribute('style', 'display: flex; gap: 6px;');

    const likeButton = document.createElement('button');
    likeButton.setAttribute('style', 'cursor: pointer; border: 1px solid #ddd; background: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;')
    likeButton.innerHTML = `👍 ${product.like_count}`;
    likeButton.classList.toggle('liked', product.is_liked);
    
    // Like button event listener
    likeButton.addEventListener('click', async function(event) {
        event.preventDefault();
        await like(item);

        // Changing innerHTML and appearance
        likeButton.innerHTML = `👍 ${product.like_count}`;
        likeButton.classList.toggle('liked', product.is_liked);
        dislikeButton.innerHTML = `👎 ${product.dislike_count}`;
        dislikeButton.classList.toggle('disliked', product.is_disliked);
    })

    // Dislike button
    const dislikeButton = document.createElement('button');
    dislikeButton.setAttribute('style', 'cursor: pointer; border: 1px solid #ddd; background: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;')
    dislikeButton.innerHTML = `👎 ${product.dislike_count}`;
    dislikeButton.classList.toggle('disliked', product.is_disliked);

    // Dislike button event listener
    dislikeButton.addEventListener('click', async function(event) {
        event.preventDefault();
        await dislike(item);

        // Changing innerHTML and appearance
        likeButton.innerHTML = `👍 ${product.like_count}`;
        likeButton.classList.toggle('liked', product.is_liked);
        dislikeButton.innerHTML = `👎 ${product.dislike_count}`;
        dislikeButton.classList.toggle('disliked', product.is_disliked);
    })

    // Appending both buttons as productActions's children
    productActions.appendChild(likeButton);
    productActions.appendChild(dislikeButton);

    return productActions;
}

async function like(item) {
    const product = item.fields;

    const likeUrl = LIKE_ITEM_ENDPOINT.replace('0', item.pk);
    
    try {
        const response = await fetch(likeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        // If response in ok, update JSON
        if (response.ok) {
            product.like_count = result.like_count;
            product.is_liked = result.is_liked;
            product.dislike_count = result.dislike_count;
            product.is_disliked = result.is_disliked;
            console.log(result.message);
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ITEM ERROR:', error);
    }
}

async function dislike(item) {
    const product = item.fields;

    const dislikeUrl = DISLIKE_ITEM_ENDPOINT.replace('0', item.pk);
    
    try {
        const response = await fetch(dislikeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        // If response in ok, update JSON
        if (response.ok) {
            product.like_count = result.like_count;
            product.is_liked = result.is_liked;
            product.dislike_count = result.dislike_count;
            product.is_disliked = result.is_disliked;
            console.log(result.message);
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ITEM ERROR:', error);
    }
}

// Fetch products data
async function fetchProducts(searchQuery = "") {
    if (productsAbortController) productsAbortController.abort();
    productsAbortController = new AbortController();

    try {
        displayPageSection({ showLoading:true });
        
        const url = searchQuery ? `${GET_ITEMS_ENDPOINT}?title=${encodeURIComponent(searchQuery)}` : GET_ITEMS_ENDPOINT;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: productsAbortController.signal,
        });

        if (!response.ok) throw new Error('Failed to fetch data');

        const productsData = await response.json();

        if (productsData.length === 0) {
            displayPageSection({ showEmpty:true });
        } else {
            gridContainer.innerHTML = '';
            productsData.forEach(item => {
                gridContainer.appendChild(buildProductCard(item));
            });
            displayPageSection({ showGrid:true });
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('ITEM ERROR:', error);
        displayPageSection({ showError:true });
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
    return cookieValue;
}

fetchProducts();
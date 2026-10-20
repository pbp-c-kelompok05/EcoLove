// Endpoint and Configs
const GRID = document.querySelector('#item-detail');

const ITEM_ID = GRID.dataset.itemId;
const LIKE_ITEM_ENDPOINT = GRID.dataset.likeItem;
const DISLIKE_ITEM_ENDPOINT = GRID.dataset.dislikeItem;

async function like() {
    const likeUrl = LIKE_ITEM_ENDPOINT.replace('0', ITEM_ID);
    
    try {
        const response = await fetch(likeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        if (response.ok) {
            console.log(result.message);
            return result;
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ITEM ERROR:', error);
        return false;
    }
}

async function dislike() {
    const dislikeUrl = DISLIKE_ITEM_ENDPOINT.replace('0', ITEM_ID);
    
    try {
        const response = await fetch(dislikeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        if (response.ok) {
            console.log(result.message);
            return result;
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ITEM ERROR:', error);
        return false;
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

// Updating like dan dislike button
function updateButtons(result) {
    likeButton.innerHTML = `👍 ${result.like_count}`;
    likeButton.classList.toggle('liked', result.is_liked);
    dislikeButton.innerHTML = `👎 ${result.dislike_count}`;
    dislikeButton.classList.toggle('disliked', result.is_disliked);
}

// Safe Event Listeners (Biar tidak crash saat user belum login)
const likeButton = document.getElementById('like-button');
const dislikeButton = document.getElementById('dislike-button');

if (likeButton && dislikeButton) {
    likeButton.addEventListener('click', async function(event) {
        event.preventDefault();
        const result = await like();
        if (result) updateButtons(result);
    });

    dislikeButton.addEventListener('click', async function(event) {
        event.preventDefault();
        const result = await dislike();
        if (result) updateButtons(result);
    });
}
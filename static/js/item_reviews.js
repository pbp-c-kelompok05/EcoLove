// DOM Elements
const loadingState = document.getElementById('loading');
const errorState = document.getElementById('error');
const emptyState = document.getElementById('empty');
const gridContainer = document.getElementById('grid');
const reviewForm = document.getElementById('review-form');

// Endpoint
const GET_REVIEWS_ENDPOINT = gridContainer.dataset.getReviewsJson;
const GET_REPLIES_ENDPOINT = gridContainer.dataset.getRepliesJson;
const LIKE_COMMENT_ENDPOINT = gridContainer.dataset.likeComment;
const DISLIKE_COMMENT_ENDPOINT = gridContainer.dataset.dislikeComment;
const ADD_REVIEW_ENDPOINT = gridContainer.dataset.addReview;
const EDIT_COMMENT_ENDPOINT = gridContainer.dataset.editComment;
const DELETE_COMMENT_ENDPOINT = gridContainer.dataset.deleteComment;
const IS_AUTHENTICATED = gridContainer.dataset.isAuthenticated === 'True';
const USER_ID = gridContainer.dataset.userId;

// Abort controller
let reviewsAbortController;

function displayPageSection({ showLoading = false, showError = false, showEmpty = false, showGrid = false }) {
    loadingState.classList.toggle('hide', !showLoading);
    errorState.classList.toggle('hide', !showError);
    emptyState.classList.toggle('hide', !showEmpty);
    gridContainer.classList.toggle('hide', !showGrid);
}

function buildCard(item) {
    const user = item.user;
    const comment = item.fields;

    const card = document.createElement('article');

    const image = comment.image
        ? `<img src="${comment.image}">`
        : '';

    const cardContent = `
        <h2>${user.name}</h2>
        ${image}
        ${comment.text}
    `;

    card.innerHTML = cardContent;
    card.appendChild(buildActions(item));

    return card;
}

function buildActions(item) {
    const comment = item.fields;

    const actions = document.createElement('div');
    actions.setAttribute('class', 'interaction-buttons');

    const likeButton = document.createElement('button');
    likeButton.innerHTML = `👍 ${comment.like_count}`;
    likeButton.classList.toggle('liked', comment.is_liked);

    likeButton.addEventListener('click', async function (event) {
        event.preventDefault();
        await likeComment(item);

        likeButton.innerHTML = `👍 ${comment.like_count}`;
        likeButton.classList.toggle('liked', comment.is_liked);
        dislikeButton.innerHTML = `👎 ${comment.dislike_count}`;
        dislikeButton.classList.toggle('disliked', comment.is_disliked);
    });

    const dislikeButton = document.createElement('button');
    dislikeButton.innerHTML = `👎 ${comment.dislike_count}`;
    dislikeButton.classList.toggle('disliked', comment.is_disliked);

    dislikeButton.addEventListener('click', async function (event) {
        event.preventDefault();
        await dislikeComment(item);

        likeButton.innerHTML = `👍 ${comment.like_count}`;
        likeButton.classList.toggle('liked', comment.is_liked);
        dislikeButton.innerHTML = `👎 ${comment.dislike_count}`;
        dislikeButton.classList.toggle('disliked', comment.is_disliked);
    });

    if(USER_ID === item.user.pk) {
        actions.appendChild(buildEditForm(item));

        const deleteButton = document.createElement('button');
        deleteButton.innerHTML = 'Delete';
        deleteButton.classList.add('disliked');
        
        deleteButton.addEventListener('click',function () { deleteComment(item); });
        actions.appendChild(deleteButton);
    }

    actions.appendChild(likeButton);
    actions.appendChild(dislikeButton);

    return actions;
}

function buildEditForm(item) {
    const comment = item.fields;

    const editForm = document.createElement('form');

    editForm.innerHTML = `
        <textarea placeholder="Edit..." name="text">${comment.text}</textarea>
        <button type="submit">Edit</button>
    `;

    editForm.addEventListener('submit', function (event) { editComment(event, item, editForm); });

    return editForm;
}

async function likeComment(item) {
    const review = item.fields;
    const likeUrl = LIKE_COMMENT_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

    try {
        const response = await fetch(likeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        if (response.ok) {
            review.like_count = result.like_count;
            review.is_liked = result.is_liked;
            review.dislike_count = result.dislike_count;
            review.is_disliked = result.is_disliked;
        } else throw new Error(result.message);
    } catch (error) {
        console.error('COMMENT ERROR:', error);
    }
}

async function dislikeComment(item) {
    const review = item.fields;
    const dislikeUrl = DISLIKE_COMMENT_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

    try {
        const response = await fetch(dislikeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        if (response.ok) {
            review.like_count = result.like_count;
            review.is_liked = result.is_liked;
            review.dislike_count = result.dislike_count;
            review.is_disliked = result.is_disliked;
        } else throw new Error(result.message);
    } catch (error) {
        console.error('COMMENT ERROR:', error);
    }
}

async function addReview(event) {
    event.preventDefault();

    const submitButton = reviewForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;

    try {
        const response = await fetch(ADD_REVIEW_ENDPOINT, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: new FormData(reviewForm),
        });
        const result = await response.json().catch(() => ({}));

        if (response.ok) {
            reviewForm.reset();
            fetchReviews();
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ERROR:', error);
    } finally {
        submitButton.disabled = false;
    }
}

async function editComment(event, item, form) {
    event.preventDefault();

    const comment = item.fields;
    const editUrl = EDIT_COMMENT_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;

    try {
        const response = await fetch(editUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: new FormData(form),
        });
        const result = await response.json().catch(() => ({}));

        if (response.ok) {
            fetchReviews();
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ERROR:', error);
    } finally {
        submitButton.disabled = false;
    }
}

async function deleteComment(item) {
    const comment = item.fields;
    const deleteUrl = DELETE_COMMENT_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

    try {
        const response = await fetch(deleteUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });
        const result = await response.json();

        if (response.ok) {
            fetchReviews();
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ERROR:', error);
    }
}

async function fetchReviews() {
    if (reviewsAbortController) reviewsAbortController.abort();
    reviewsAbortController = new AbortController();

    try {
        displayPageSection({ showLoading: true });

        const response = await fetch(GET_REVIEWS_ENDPOINT, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: reviewsAbortController.signal,
        });

        if (!response.ok) throw new Error('Failed to fetch data');

        const reviewsData = await response.json();

        if (reviewsData.length === 0) {
            displayPageSection({ showEmpty: true });
        } else {
            gridContainer.innerHTML = '';
            reviewsData.forEach(item => {
                gridContainer.appendChild(buildCard(item));
            });
            displayPageSection({ showGrid: true });
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('ERROR:', error);
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

// Review form event handler
reviewForm.addEventListener('submit', addReview);

fetchReviews();
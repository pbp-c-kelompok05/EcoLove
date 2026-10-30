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
const EDIT_REVIEW_ENDPOINT = gridContainer.dataset.editReview;
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

function buildReviewCard(item) {
    const user = item.user;
    const review = item.fields;

    const card = document.createElement('article');

    const image = review.image
        ? `<img src="${review.image}">`
        : '';

    const cardContent = `
        <h2>${user.name} (⭐${review.rating})</h2>
        ${image}
        <p>${review.text}<p>
    `;

    card.innerHTML = cardContent;
    card.appendChild(buildReviewActions(item, card));

    return card;
}

function buildReviewActions(item, parent) {
    const review = item.fields;

    const actions = document.createElement('div');
    actions.setAttribute('class', 'interaction-buttons');

    const likeButton = document.createElement('button');
    likeButton.innerHTML = `👍 ${review.like_count}`;
    likeButton.classList.toggle('liked', review.is_liked);

    likeButton.addEventListener('click', async function (event) {
        event.preventDefault();
        likeButton.disabled = true;

        if (await likeComment(item)) {
            likeButton.innerHTML = `👍 ${review.like_count}`;
            likeButton.classList.toggle('liked', review.is_liked);
            dislikeButton.innerHTML = `👎 ${review.dislike_count}`;
            dislikeButton.classList.toggle('disliked', review.is_disliked);
        }

        likeButton.disabled = false;
    });

    const dislikeButton = document.createElement('button');
    dislikeButton.innerHTML = `👎 ${review.dislike_count}`;
    dislikeButton.classList.toggle('disliked', review.is_disliked);

    dislikeButton.addEventListener('click', async function (event) {
        event.preventDefault();
        dislikeButton.disabled = true;

        if (await dislikeComment(item)) {
            likeButton.innerHTML = `👍 ${review.like_count}`;
            likeButton.classList.toggle('liked', review.is_liked);
            dislikeButton.innerHTML = `👎 ${review.dislike_count}`;
            dislikeButton.classList.toggle('disliked', review.is_disliked);
        }

        dislikeButton.disabled = false;
    });

    if(USER_ID === item.user.pk) {
        const editForm = buildReviewEditForm(item);
        
        editForm.addEventListener('submit', async function (event) {
            event.preventDefault();

            if (validateEditReviewForm(editForm, item) && await editReview(item, editForm)) {
                parent.querySelector('h2').innerHTML = `${item.user.name} (⭐${review.rating})`;
                parent.querySelector('p').innerHTML = review.text;
            }
        });

        const deleteButton = document.createElement('button');
        deleteButton.innerHTML = 'Delete';
        deleteButton.classList.add('disliked');
        
        deleteButton.addEventListener('click', async function () {
            if (await deleteComment(item)) parent.remove();
        });

        actions.appendChild(editForm);
        actions.appendChild(deleteButton);
    }

    actions.appendChild(likeButton);
    actions.appendChild(dislikeButton);

    return actions;
}

function buildReviewEditForm(item) {
    const review = item.fields;

    const editForm = document.createElement('form');

    editForm.innerHTML = `
        <textarea placeholder="Edit..." name="text">${review.text}</textarea>
        <select name="rating" value=${review.rating}>
            <option>5</option>
            <option>4</option>
            <option>3</option>
            <option>2</option>
            <option>1</option>
        </select>
        <button type="submit">Edit</button>
    `;

    editForm.querySelector('select').selectedIndex = 5-review.rating;

    return editForm;
}

async function likeComment(item) {
    const comment = item.fields;
    const likeUrl = LIKE_COMMENT_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

    try {
        const response = await fetch(likeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        if (response.ok) {
            comment.like_count = result.like_count;
            comment.is_liked = result.is_liked;
            comment.dislike_count = result.dislike_count;
            comment.is_disliked = result.is_disliked;
            return true;
        } else throw new Error(result.message);
    } catch (error) {
        console.error('COMMENT ERROR:', error);
    }
}

async function dislikeComment(item) {
    const comment = item.fields;
    const dislikeUrl = DISLIKE_COMMENT_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

    try {
        const response = await fetch(dislikeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        const result = await response.json();

        if (response.ok) {
            comment.like_count = result.like_count;
            comment.is_liked = result.is_liked;
            comment.dislike_count = result.dislike_count;
            comment.is_disliked = result.is_disliked;
            return true;
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
            gridContainer.insertBefore(buildReviewCard(result.review), gridContainer.firstChild);
        } else throw new Error(result.message);
    } catch (error) {
        console.error('ERROR:', error);
    } finally {
        submitButton.disabled = false;
    }
}

async function editReview(item, form) {
    const review = item.fields;
    const editUrl = EDIT_REVIEW_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', item.pk);

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
            review.text = result.text;
            review.rating = result.rating;
            return true;
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

        if (response.ok) return true;
        else throw new Error(result.message);
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
                gridContainer.appendChild(buildReviewCard(item));
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

function validateReviewForm() {
    return (reviewForm.querySelector('textarea').value &&
        reviewForm.querySelector('select').selectedIndex > 0 &&
        reviewForm.querySelector('select').selectedIndex < 6);
}

function validateEditReviewForm(form, item) {
    const review = item.fields;
    return (form.querySelector('textarea').value &&
        form.querySelector('select').selectedIndex > -1 &&
        form.querySelector('select').selectedIndex < 5 &&
        form.querySelector('textarea').value != review.text ||
        form.querySelector('select').selectedIndex != 5-review.rating);
}

// Review form event handler
reviewForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (validateReviewForm()) addReview(event);
});

fetchReviews();
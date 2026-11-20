// DOM Elements
const loadingState = document.getElementById('loading');
const errorState = document.getElementById('error');
const emptyState = document.getElementById('empty');
const gridContainer = document.getElementById('grid');
const reviewForm = document.getElementById('review-form');
const reviewFormContainer = document.getElementById('review-form-container');

// Endpoint
const REVIEW_LIST_ENDPOINT = gridContainer.dataset.reviewList;
const REVIEW_DETAIL_ENDPOINT = gridContainer.dataset.reviewDetail;
const REVIEW_LIKE_ENDPOINT = gridContainer.dataset.like;
const REVIEW_DISLIKE_ENDPOINT = gridContainer.dataset.dislike;
const IS_AUTHENTICATED = gridContainer.dataset.isAuthenticated === 'True';

// Abort controller
let reviewsAbortController;

function displayPageSection(
    {
        showLoading = false,
        showError = false,
        showEmpty = false,
        showGrid = false,
        showForm = false
    }
) {
    loadingState.classList.toggle('hide', !showLoading);
    errorState.classList.toggle('hide', !showError);
    emptyState.classList.toggle('hide', !showEmpty);
    gridContainer.classList.toggle('hide', !showGrid);
    if (reviewFormContainer) reviewFormContainer.classList.toggle('hide', !showForm);
}

function buildReviewCard(review) {
    const card = document.createElement('article');
    card.className = 'review';

    const cardContent = `
        <h2>${review.owner} (⭐${review.rating})</h2>
        <p>${review.text}</p>
    `;

    card.innerHTML = cardContent;

    if(review.is_owner) {
        const editForm = buildReviewEditForm(review);
        
        editForm.addEventListener('submit', async function (event) {
            event.preventDefault();

            if (validateEditReviewForm(editForm, review) && await editReview(review, editForm)) {
                card.querySelector('h2').innerHTML = `${review.owner} (⭐${review.rating})`;
                card.querySelector('p').innerHTML = review.text;
            }
        });

        card.appendChild(editForm);
    }

    card.appendChild(buildReviewActions(review, card));

    return card;
}

function buildReviewActions(review, parent) {
    const actions = document.createElement('div');
    actions.className = 'interaction-buttons';

    const likeButton = document.createElement('button');
    likeButton.innerHTML = `👍 ${review.like_count}`;
    likeButton.classList.toggle('liked', review.is_liked);

    const dislikeButton = document.createElement('button');
    dislikeButton.innerHTML = `👎 ${review.dislike_count}`;
    dislikeButton.classList.toggle('disliked', review.is_disliked);

    if (IS_AUTHENTICATED) {
        likeButton.addEventListener('click', async function (event) {
            event.preventDefault();
            likeButton.disabled = true;

            if (await likeReview(review)) {
                likeButton.innerHTML = `👍 ${review.like_count}`;
                likeButton.classList.toggle('liked', review.is_liked);
                dislikeButton.innerHTML = `👎 ${review.dislike_count}`;
                dislikeButton.classList.toggle('disliked', review.is_disliked);
            }

            likeButton.disabled = false;
        });

        dislikeButton.addEventListener('click', async function (event) {
            event.preventDefault();
            dislikeButton.disabled = true;

            if (await dislikeReview(review)) {
                likeButton.innerHTML = `👍 ${review.like_count}`;
                likeButton.classList.toggle('liked', review.is_liked);
                dislikeButton.innerHTML = `👎 ${review.dislike_count}`;
                dislikeButton.classList.toggle('disliked', review.is_disliked);
            }

            dislikeButton.disabled = false;
        });
    } else {
        likeButton.disabled = true;
        dislikeButton.disabled = true;
    }
    

    if(review.is_deletable) {
        const deleteButton = document.createElement('button');
        deleteButton.innerHTML = 'Delete';
        deleteButton.classList.add('disliked');
        
        deleteButton.addEventListener('click', async function () {
            if (await deleteReview(review)) {
                parent.remove();
                if (review.is_owner) displayPageSection({ showGrid: true, showForm: true});
            }
        });

        actions.appendChild(deleteButton);
    }

    actions.appendChild(likeButton);
    actions.appendChild(dislikeButton);

    return actions;
}

function buildReviewEditForm(review) {
    const editForm = document.createElement('form');
    editForm.className = 'review';

    editForm.innerHTML = `
        <h2>Edit Review<h2>
        <textarea placeholder="Edit..."
                  name="text"
                  class="review">${review.text}</textarea>
        ⭐
        <select name="rating" class="review">
            <option>5</option>
            <option>4</option>
            <option>3</option>
            <option>2</option>
            <option>1</option>
        </select>
        <button type="submit" class="btn btn-primary">Edit</button>
    `;

    editForm.querySelector('select').selectedIndex = 5-review.rating;

    return editForm;
}

async function likeReview(review) {
    const likeUrl = REVIEW_LIKE_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', review.id);

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
            return true;
        } else throw new Error(`HTTP ${response.status}`);
    } catch (error) {
        console.error('COMMENT ERROR:', error);
    }
}

async function dislikeReview(review) {
    const dislikeUrl = REVIEW_DISLIKE_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', review.id);

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
            return true;
        } else throw new Error(`HTTP ${response.status}`);
    } catch (error) {
        console.error('COMMENT ERROR:', error);
    }
}

async function addReview(event) {
    event.preventDefault();

    const submitButton = reviewForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;

    try {
        const response = await fetch(REVIEW_LIST_ENDPOINT, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: new FormData(reviewForm),
        });
        const result = await response.json().catch(() => ({}));

        if (response.ok) {
            reviewForm.reset();
            gridContainer.insertBefore(buildReviewCard(result), gridContainer.firstChild);
            displayPageSection({ showGrid: true, showForm: false})
        } else throw new Error(`HTTP ${response.status}`);
    } catch (error) {
        console.error('ERROR:', error);
    } finally {
        submitButton.disabled = false;
    }
}

async function editReview(review, form) {
    const editUrl = REVIEW_DETAIL_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', review.id);

    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;

    try {
        const response = await fetch(editUrl, {
            method: 'PATCH',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: new FormData(form),
        });
        const result = await response.json().catch(() => ({}));

        if (response.ok) {
            review.text = result.text;
            review.rating = result.rating;
            return true;
        } else throw new Error(`HTTP ${response.status}`);
    } catch (error) {
        console.error('ERROR:', error);
    } finally {
        submitButton.disabled = false;
    }
}

async function deleteReview(review) {
    const deleteUrl = REVIEW_DETAIL_ENDPOINT.replace('00000000-0000-0000-0000-000000000000', review.id);

    try {
        const response = await fetch(deleteUrl, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });

        if (response.ok) return true;
        else throw new Error(`HTTP ${response.status}`);
    } catch (error) {
        console.error('ERROR:', error);
    }
}

async function fetchReviews() {
    if (reviewsAbortController) reviewsAbortController.abort();
    reviewsAbortController = new AbortController();

    try {
        displayPageSection({ showLoading: true });

        const response = await fetch(REVIEW_LIST_ENDPOINT, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: reviewsAbortController.signal,
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reviewsData = await response.json();

        if (reviewsData.length === 0) {
            displayPageSection({ showEmpty: true, showForm: true });
        } else {
            var show = IS_AUTHENTICATED;
            const arr = [];
            gridContainer.innerHTML = '';
            reviewsData.forEach(item => {
                if (item.is_owner) {
                    show = false;
                    gridContainer.appendChild(buildReviewCard(item));
                } else {
                    arr.push(buildReviewCard(item))
                }
            });
            arr.forEach(item => gridContainer.appendChild(item));
            displayPageSection({ showGrid: true, showForm: show });
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

function validateEditReviewForm(form, review) {
    return (form.querySelector('textarea').value &&
        form.querySelector('select').selectedIndex > -1 &&
        form.querySelector('select').selectedIndex < 5 &&
        form.querySelector('textarea').value != review.text ||
        form.querySelector('select').selectedIndex != 5-review.rating);
}

// Review form event handler
if (reviewForm) {
    reviewForm.addEventListener('submit', function (event) {
        event.preventDefault();
        if (validateReviewForm()) addReview(event);
    });
}

fetchReviews();
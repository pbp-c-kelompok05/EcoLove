// DOM elements
const imageInput = document.querySelector('#id_image');
const imageDClearCheckbox = document.querySelector('#image-clear_id')
const imagePreview = document.querySelector('img');
const imageRemove = document.querySelector('#remove_id');
const imageUndoChanges = document.querySelector('#undo_changes_id');

// Initial image path
const imagePath = imagePreview.src;

function addImage(event) {
    imagePreview.src = URL.createObjectURL(event.target.files[0]);
    imagePreview.classList.toggle('hide', false);
    imageRemove.classList.toggle('hide', false);
    if(imageUndoChanges) imageUndoChanges.classList.toggle('hide', false);
    if(imageDClearCheckbox) imageDClearCheckbox.checked = false;
}

function removeImage() {
    imageInput.value = null;
    imagePreview.classList.toggle('hide', true);
    imageRemove.classList.toggle('hide', true);
    if(imageUndoChanges) imageUndoChanges.classList.toggle('hide', false);
    if(imageDClearCheckbox) imageDClearCheckbox.checked = true;
}

function undoChanges() {
    imageInput.value = null;
    imagePreview.src = imagePath;
    imagePreview.classList.toggle('hide', false);
    imageRemove.classList.toggle('hide', false);
    imageUndoChanges.classList.toggle('hide', true);
    if(imageDClearCheckbox) imageDClearCheckbox.checked = false;
}

if (imagePath) {
    imagePreview.classList.toggle('hide', false);
    imageRemove.classList.toggle('hide', false);
}
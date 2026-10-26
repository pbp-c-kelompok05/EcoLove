const form = document.querySelector('form');
const formImageInput = form.querySelector('#image-input');
const formImagePreview = form.querySelector('img');
const formImageDelete = form.querySelector('button[type="button"]');

formImageInput.addEventListener(
    'input',
    function(event) {
        formImagePreview.src = URL.createObjectURL(event.target.files[0]);
        formImagePreview.classList.toggle('hide', false);
        formImageDelete.classList.toggle('hide', false);
    }
)

function removeImage() {
    formImageInput.value = null;
    formImagePreview.attributes.src = null;
    formImagePreview.classList.toggle('hide', true);
    formImageDelete.classList.toggle('hide', true);
}
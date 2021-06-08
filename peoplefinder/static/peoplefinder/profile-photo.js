/**
 * # Profile photo web component
 *
 * ## Attributes
 *
 * ### `name`
 * Name given to the input which will be submitted.
 *
 * ### `photo-url`
 * URL for the current profile photo.
 *
 * ### `x-name`
 * Name given to the x crop input which will be submitted.
 *
 * ### `y-name`
 * Name given to the y crop input which will be submitted.
 * 
 * ### `width-name`
 * Name given to the width crop input which will be submitted.
 * 
 * ### `height-name`
 * Name given to the height crop input which will be submitted.
 *
 * ## Notes
 * - does not use a shadow dom
 *   - so we can use GDS styles
 *   - and the input can be submitted
 */
class ProfilePhoto extends HTMLElement {
    constructor() {
        super();

        this.validFileExtensions = ['jpeg', 'jpg', 'png'];

        this.cropper = null;

        // binding methods
        this.handleChangePhoto = this.handleChangePhoto.bind(this);
        this.setErrors = this.setErrors.bind(this);
        this.clearErrors = this.clearErrors.bind(this);
    }

    connectedCallback() {
        this.name = this.getAttribute('name');
        this.photoUrl = this.getAttribute('photo-url') || "";
        this.cropFieldNames = {
            x: this.getAttribute('x-name'),
            y: this.getAttribute('y-name'),
            width: this.getAttribute('width-name'),
            height: this.getAttribute('height-name'),
        }

        this.innerHTML = `
            <div class="govuk-grid-row">
                <div class="govuk-grid-column-one-third">
                    <h3 class="govuk-heading-s" id="photo-heading">Current profile photo</h3>
                    <div>
                        <img
                            src="${this.photoUrl}"
                            id="profile-photo"
                            style="display: block; max-width: 100%;"
                        >
                    </div>
                </div>
                <div class="govuk-grid-column-two-thirds">
                    <div class="govuk-form-group" id="photo-form-group">
                        <label class="govuk-label" for="photo">
                            Choose a new profile photo
                        </label>
                        <span class="govuk-hint">
                            Choose a picture that helps others recognise you.
                            Your picture must be at least 500 by 500 pixels and no more than 8MB.
                            Once you have chosen a picture, you will be able to crop it.
                        </span>
                        <div id="photo-errors"></div>
                        <input
                            class="govuk-file-upload"
                            type="file"
                            name="${this.name}"
                            id="photo"
                        >
                    </div>
                </div>
            </div>
            <div>
                <input type="hidden" name="${this.cropFieldNames.x}">
                <input type="hidden" name="${this.cropFieldNames.y}">
                <input type="hidden" name="${this.cropFieldNames.width}">
                <input type="hidden" name="${this.cropFieldNames.height}">
            </div>
        `;

        this.photoHeadingEl = this.querySelector('#photo-heading');
        this.photoImgEl = this.querySelector('#profile-photo');
        this.photoFormGroupEl = this.querySelector('#photo-form-group');
        this.photoErrorsEl = this.querySelector('#photo-errors');
        this.photoInputEl = this.querySelector('#photo');
        this.xEl = this.querySelector(`[name="${this.cropFieldNames.x}"]`);
        this.yEl = this.querySelector(`[name="${this.cropFieldNames.y}"]`);
        this.widthEl = this.querySelector(`[name="${this.cropFieldNames.width}"]`);
        this.heightEl = this.querySelector(`[name="${this.cropFieldNames.height}"]`);

        this.photoInputEl.addEventListener('change', this.handleChangePhoto);
    }

    handleChangePhoto(e) {
        if (this.cropper) {
            this.cropper.destroy();
            this.cropper = null;
        }

        const file = e.target.files[0];
        const fileExt = file.name.split('.').pop();

        const errors = [];

        if (!this.validFileExtensions.find(ext => ext === fileExt.toLowerCase())) {
            errors.push('This file is not an accepted image format. Please choose a JPG or PNG file.');
        }

        this.clearErrors();

        if (errors.length) {
            this.setErrors(errors);
            this.photoInputEl.value = null;
            return
        }

        const syncCropperWithInputs = _ => {
            const cropperData = this.cropper.getData();
            
            this.xEl.value = Math.round((cropperData.x));
            this.yEl.value = Math.round((cropperData.y));
            this.widthEl.value = Math.round((cropperData.width));
            this.heightEl.value = Math.round((cropperData.height));
        };

        const reader = new FileReader();
        reader.onload = e => {
            let errors = [];

            // seems it is not exact because it's close enough
            const fileSize = e.target.total / 1024 / 1024;

            if (fileSize > 8) {
                errors.push('Photo file size is greater than 8MB');
            }

            const imgDataURL = e.target.result;
            // build an image object so we can use onload to check width and height
            const newImgEl = new Image();
            newImgEl.src = imgDataURL;
            newImgEl.onload = e => {
                if (newImgEl.naturalWidth < 500) {
                    errors.push('Photo width is less than 500px');
                }

                if (newImgEl.naturalHeight < 500) {
                    errors.push('Photo height is less than 500px');
                }

                if (errors.length) {
                    this.setErrors(errors);
                    this.photoInputEl.value = null;
                    return
                }

                // don't replace with the new image element just reuse the old one
                this.photoImgEl.src = imgDataURL;

                this.cropper = new DW.peoplefinder.Cropper(this.photoImgEl, {
                    // square
                    aspectRatio: 1 / 1,
                    movable: false,
                    rotatable: false,
                    scalable: false,
                    zoomable: false,
                    zoomOnTouch: false,
                    zoomOnWheel: false,
                    ready: syncCropperWithInputs,
                    cropend: syncCropperWithInputs,
                });    
            }
        };

        reader.readAsDataURL(file);

        this.photoHeadingEl.innerHTML = 'Crop new profile photo';
    }

    setErrors(errors) {
        this.photoFormGroupEl.classList.add('govuk-form-group--error');
        this.photoErrorsEl.innerHTML = errors.map(error => {
            return `
                <span class="govuk-error-message">
                    <span class="govuk-visually-hidden">Error:</span>
                    ${error}
                </span>
            `;
        }).join('');
    }

    clearErrors() {
        this.photoFormGroupEl.classList.remove('govuk-form-group--error');
        this.photoErrorsEl.innerHTML = '';
    }
}

customElements.define('profile-photo', ProfilePhoto);

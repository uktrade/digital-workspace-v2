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
 * ### `no-photo-url`
 * URL for the image to use when the profile has no photo.
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
 * ### `remove-photo-name`
 * Name given to the remove photo checkbox input which will be submitted.
 *
 * ## Notes
 * - does not use a shadow dom
 *   - so we can use GDS styles
 *   - and the input can be submitted
 */
class ProfilePhoto extends HTMLElement {
  constructor() {
    super();

    this.validFileExtensions = ["jpeg", "jpg", "png"];

    this.cropper = null;

    // binding methods
    this.handleChangePhoto = this.handleChangePhoto.bind(this);
    this.handleClearImage = this.handleClearImage.bind(this);
    this.setErrors = this.setErrors.bind(this);
    this.clearErrors = this.clearErrors.bind(this);
  }

  connectedCallback() {
    this.name = this.getAttribute("name");
    this.photoUrl = this.getAttribute("photo-url") || "";
    this.noPhotoUrl = this.getAttribute("no-photo-url");
    this.cropFieldNames = {
      x: this.getAttribute("x-name"),
      y: this.getAttribute("y-name"),
      width: this.getAttribute("width-name"),
      height: this.getAttribute("height-name"),
    };
    this.removePhotoName = this.getAttribute("remove-photo-name");

    // Replace innerHTML
    this.buildPhotoComponent();

    this.photoHeadingEl = this.querySelector("#photo-heading");
    this.photoImgEl = this.querySelector("#profile-photo");
    this.photoFormGroupEl = this.querySelector("#photo-form-group");
    this.photoErrorsEl = this.querySelector("#photo-errors");
    this.photoInputEl = this.querySelector("#photo");
    this.clearImageEl = this.querySelector("#clear-image");
    this.removePhotoWrapperEl = this.querySelector("#remove-photo-wrapper");
    this.removePhotoEl = this.querySelector("#remove-photo");
    this.xEl = this.querySelector(`[name="${this.cropFieldNames.x}"]`);
    this.yEl = this.querySelector(`[name="${this.cropFieldNames.y}"]`);
    this.widthEl = this.querySelector(`[name="${this.cropFieldNames.width}"]`);
    this.heightEl = this.querySelector(
      `[name="${this.cropFieldNames.height}"]`
    );

    if (this.photoUrl) {
      // this.removePhotoWrapperEl.style.display = "block";
      this.clearImageEl.style.display = "inline";
    }

    this.photoInputEl.addEventListener("change", this.handleChangePhoto);
    this.clearImageEl.addEventListener("click", this.handleClearImage);
  }

  buildPhotoComponent() {
    const photoHeadingText = this.photoUrl
      ? "Current profile photo"
      : "No current profile photo";

    const photoHeading = document.createElement("h3");
    photoHeading.classList.add("govuk-heading-s");
    photoHeading.id = "photo-heading";
    photoHeading.textContent = photoHeadingText;
    this.appendChild(photoHeading);

    const cropperWrapper = document.createElement("div");
    cropperWrapper.classList.add("cropper-wrapper");
    cropperWrapper.style.maxWidth = "300px";

    const photoImg = document.createElement("img");
    photoImg.src = this.photoUrl || this.noPhotoUrl;
    photoImg.id = "profile-photo";
    photoImg.style.display = "block";
    photoImg.style.maxWidth = "100%";
    cropperWrapper.appendChild(photoImg);
    this.appendChild(cropperWrapper);

    const formGroup = document.createElement("div");
    formGroup.classList.add("govuk-form-group");
    formGroup.id = "photo-form-group";

    const label = document.createElement("label");
    label.classList.add("govuk-label");
    label.setAttribute("for", "photo");
    label.textContent = "Choose a new profile photo";
    formGroup.appendChild(label);

    const hint = document.createElement("div");
    hint.classList.add("govuk-hint");
    hint.textContent =
      "Choose a picture that helps others recognise you. " +
      "Your picture must be at least 500 by 500 pixels and no more than 8MB. " +
      "Once you have chosen a picture, you will be able to crop it.";
    formGroup.appendChild(hint);

    const errorsDiv = document.createElement("div");
    errorsDiv.id = "photo-errors";
    formGroup.appendChild(errorsDiv);

    const photoInput = document.createElement("input");
    photoInput.classList.add("govuk-file-upload");
    photoInput.type = "file";
    photoInput.name = this.name;
    photoInput.id = "photo";
    formGroup.appendChild(photoInput);

    const lineBreak = document.createElement("br");
    formGroup.appendChild(lineBreak);

    const clearImageButton = document.createElement("button");
    clearImageButton.type = "button";
    clearImageButton.id = "clear-image";
    clearImageButton.classList.add("dwds-button", "dwds-button--secondary");
    clearImageButton.style.display = "none";
    clearImageButton.textContent = "Clear image";
    formGroup.appendChild(clearImageButton);

    const removePhotoWrapper = document.createElement("div");
    removePhotoWrapper.classList.add(
      "govuk-checkboxes",
      "govuk-checkboxes--small"
    );
    removePhotoWrapper.id = "remove-photo-wrapper";
    removePhotoWrapper.style.display = "none";

    const removePhotoItem = document.createElement("div");
    removePhotoItem.classList.add("govuk-checkboxes__item");

    const removePhotoCheckbox = document.createElement("input");
    removePhotoCheckbox.classList.add("govuk-checkboxes__input");
    removePhotoCheckbox.type = "checkbox";
    removePhotoCheckbox.id = "remove-photo";
    removePhotoCheckbox.name = this.removePhotoName;
    removePhotoCheckbox.value = "True";
    removePhotoItem.appendChild(removePhotoCheckbox);

    const removePhotoLabel = document.createElement("label");
    removePhotoLabel.classList.add("govuk-label", "govuk-checkboxes__label");
    removePhotoLabel.setAttribute("for", "remove-photo");
    removePhotoLabel.textContent = "Remove photo";
    removePhotoItem.appendChild(removePhotoLabel);

    removePhotoWrapper.appendChild(removePhotoItem);
    formGroup.appendChild(removePhotoWrapper);

    this.appendChild(formGroup);

    const hiddenFields = ["x", "y", "width", "height"].map((field) => {
      const inputEl = document.createElement("input");
      inputEl.type = "hidden";
      inputEl.name = this.cropFieldNames[field];
      return inputEl;
    });

    hiddenFields.forEach((hiddenField) => this.appendChild(hiddenField));
  }

  handleChangePhoto(e) {
    if (this.cropper) {
      this.cropper.destroy();
      this.cropper = null;
    }

    const file = e.target.files[0];
    const fileExt = file.name.split(".").pop();

    const errors = [];

    if (
      !this.validFileExtensions.find((ext) => ext === fileExt.toLowerCase())
    ) {
      errors.push(
        "This file is not an accepted image format. Please choose a JPG or PNG file."
      );
    }

    this.clearErrors();

    if (errors.length) {
      this.setErrors(errors);
      this.photoInputEl.value = null;
      return;
    }

    const syncCropperWithInputs = (_) => {
      const cropperData = this.cropper.getData();

      this.xEl.value = Math.round(cropperData.x);
      this.yEl.value = Math.round(cropperData.y);
      this.widthEl.value = Math.round(cropperData.width);
      this.heightEl.value = Math.round(cropperData.height);
    };

    const reader = new FileReader();
    reader.onload = (e) => {
      let errors = [];

      // seems it is not exact because it's close enough
      const fileSize = e.target.total / 1024 / 1024;

      if (fileSize > 8) {
        errors.push("Photo file size is greater than 8MB");
      }

      const imgDataURL = e.target.result;
      // build an image object so we can use onload to check width and height
      const newImgEl = new Image();
      newImgEl.src = imgDataURL;
      newImgEl.onload = (e) => {
        if (newImgEl.naturalWidth < 500) {
          errors.push("Photo width is less than 500px");
        }

        if (newImgEl.naturalHeight < 500) {
          errors.push("Photo height is less than 500px");
        }

        if (errors.length) {
          this.setErrors(errors);
          this.photoInputEl.value = null;
          return;
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
      };
    };

    reader.readAsDataURL(file);

    // Mark the photo for upload
    this.removePhotoEl.checked = false;

    this.photoHeadingEl.innerHTML = "Crop new profile photo";
    this.clearImageEl.style.display = "inline";
  }

  handleClearImage(e) {
    if (this.cropper) {
      this.cropper.destroy();
      this.cropper = null;
    }

    this.clearErrors();

    this.photoInputEl.value = null;
    // We must reset the supporting inputs or else the form will think something has
    // changed.
    this.xEl.value = "";
    this.yEl.value = "";
    this.widthEl.value = "";
    this.heightEl.value = "";
    this.photoImgEl.src = this.noPhotoUrl;
    this.clearImageEl.style.display = "none";

    // Mark the photo for deletion
    this.removePhotoEl.checked = true;

    this.photoHeadingEl.innerHTML = "No current profile photo";
  }

  setErrors(errors) {
    this.photoFormGroupEl.classList.add("govuk-form-group--error");
    this.photoErrorsEl.innerHTML = errors
      .map((error) => {
        return `
                <p class="govuk-error-message">
                    <span class="govuk-visually-hidden">Error:</span>
                    ${error}
                </p>
            `;
      })
      .join("");
  }

  clearErrors() {
    this.photoFormGroupEl.classList.remove("govuk-form-group--error");
    this.photoErrorsEl.innerHTML = "";
  }
}

customElements.define("profile-photo", ProfilePhoto);

document.addEventListener('DOMContentLoaded', function () {
    const fbButton = document.querySelector('.dwds-sidebar-feedback button');
    const fbElement = document.querySelector('.feedback-section details');
    fbButton.addEventListener('click', function (event) {
        event.preventDefault();
        fbElement.open = true;
        fbElement.querySelector('*').focus();
    });
});
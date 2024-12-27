document.addEventListener('DOMContentLoaded', function () {
    const feedbackButton = document.querySelector('.dwds-sidebar-feedback button');
    const feedbackElement = document.querySelector('.feedback-section details');
    const feedbackInput = feedbackElement.querySelector('#id_trying_to');
    feedbackButton.addEventListener('click', function (event) {
        event.preventDefault();
        feedbackElement.open = true;
        feedbackInput.focus();
    });
});
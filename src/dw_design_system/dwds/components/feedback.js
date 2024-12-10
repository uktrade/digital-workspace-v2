document.addEventListener('DOMContentLoaded', function () {
    const fbButton = document.querySelector('.feedback-btn');
    const fbElement = document.querySelector('.feedback-section details');
    fbButton.addEventListener('click', function(event) {
        event.preventDefault();
        fbElement.open = true;
        fbElement.scrollIntoView({ behavior: 'smooth' });
    });
});
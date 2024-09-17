const ribbons = document.querySelectorAll('.dwds-ribbon');

function resizeSpacer(ribbon) {
    const ribbonMain = ribbon.querySelector('.ribbon-main');
    const ribbonSpacer = ribbon.querySelector('.ribbon-spacer');

    ribbonSpacer.style.height = ribbonMain.clientHeight + 'px';
    ribbonSpacer.style.width = ribbonMain.clientWidth + 'px';
}

window.addEventListener('resize', () => {
    ribbons.forEach(ribbon => {
        resizeSpacer(ribbon);
    });
});

ribbons.forEach(ribbon => {
    resizeSpacer(ribbon);
});
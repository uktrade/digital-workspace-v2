function setRibbonMainHeight(ribbonMain) {
    var ribbonMainHeight = ribbonMain.getBoundingClientRect().height;
    ribbonMain.style.setProperty('--ribbon-main-height', ribbonMainHeight + 'px');
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.ribbon-main').forEach(function (ribbonMain) {
        setRibbonMainHeight(ribbonMain);
        window.addEventListener('resize', function () {
            setRibbonMainHeight(ribbonMain);
        });
    });
});

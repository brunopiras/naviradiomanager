// audio_handler.js
const stopOtherAudio = (event) => {
    const allAudios = window.parent.document.querySelectorAll('audio');
    allAudios.forEach(audio => {
        if (audio !== event.target) {
            audio.pause();
            audio.currentTime = 0;
        }
    });
};

const observer = new MutationObserver(() => {
    const audios = window.parent.document.querySelectorAll('audio');
    audios.forEach(audio => {
        audio.removeEventListener('play', stopOtherAudio);
        audio.addEventListener('play', stopOtherAudio);
    });
});

observer.observe(window.parent.document.body, { childList: true, subtree: true });

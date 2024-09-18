document.addEventListener('DOMContentLoaded', function () {
    const texts = ["I want to write my name", "Where is the list?", "I need the class list for my course", "Where's attendance for last class?"];
    let index = 0;
    let charIndex = 0;
    const typewriterElement = document.getElementById('typewriter');
    const typingSpeed = 100; // Adjust typing speed here
    const delayBetweenTexts = 2500; // Delay between texts

    function type() {
        if (charIndex < texts[index].length) {
            typewriterElement.textContent += texts[index].charAt(charIndex);
            charIndex++;
            setTimeout(type, typingSpeed);
        } else {
            setTimeout(erase, delayBetweenTexts);
        }
    }

    function erase() {
        if (charIndex > 0) {
            typewriterElement.textContent = texts[index].substring(0, charIndex - 1);
            charIndex--;
            setTimeout(erase, typingSpeed);
        } else {
            index = (index + 1) % texts.length;
            setTimeout(type, typingSpeed);
        }
    }

    type();
});
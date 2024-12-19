document.addEventListener('DOMContentLoaded', () => {
    const defaultAccordionGroup = document.querySelector('.accordion-group[data-accordion="default-accordion"]');
    if (defaultAccordionGroup) {
        defaultAccordion(defaultAccordionGroup);
    }
});

function defaultAccordion(defaultAccordionGroup) {

    const accordionButtons = defaultAccordionGroup.querySelectorAll('.accordion-toggle');

    accordionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const accordion = button.parentElement;
            const content = button.nextElementSibling;
            const isOpen = content.style.maxHeight !== '';

            if (isOpen) {
                close(button);
                content.style.maxHeight = '';
                accordion.classList.remove('active');
            } else {
                content.style.maxHeight = content.scrollHeight + 'px';
                accordion.classList.add('active');
                const otherButtons = defaultAccordionGroup.querySelectorAll('.accordion-toggle');
                otherButtons.forEach(otherButton => {
                    if (otherButton !== button) {
                        const otherAccordion = otherButton.parentElement;
                        otherAccordion.classList.remove('active');
                        close(otherButton, accordion);
                    }
                });
            }
        });
    });
}

function close(element, accordion) {
    const content = element.nextElementSibling;
    content.style.maxHeight = '';
}
document.addEventListener('DOMContentLoaded', function() {
    const ctaButton = document.querySelector('.cta-button');
    if (ctaButton) {
        ctaButton.addEventListener('click', function() {
            alert('Getting started!');
        });
    }

    // Mengensteuerung für Artikel
    const quantityInput = document.getElementById('item-quantity');
    const decreaseButton = document.getElementById('decrease-quantity');
    const increaseButton = document.getElementById('increase-quantity');

    // Prüfen ob die Elemente existieren
    if (quantityInput && decreaseButton && increaseButton) {
        // Event-Listener für den "Verringern"-Button
        decreaseButton.addEventListener('click', function() {
            const currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
            }
        });

        // Event-Listener für den "Erhöhen"-Button
        increaseButton.addEventListener('click', function() {
            const currentValue = parseInt(quantityInput.value);
            quantityInput.value = currentValue + 1;
        });

        // Direkte Eingabe validieren
        quantityInput.addEventListener('change', function() {
            const value = parseInt(this.value);
            if (value < 1) this.value = 1;
        });
    }
});

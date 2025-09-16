document.addEventListener('DOMContentLoaded', function() {
    // Function to show the correct tab content on page load
    function initializeTabs() {
        const premiumTab = document.getElementById('premium-tab');
        const freeTab = document.getElementById('free-tab');

        if (premiumTab.checked) {
            showTab('premium-content-section');
        } else if (freeTab.checked) {
            showTab('free-content-section');
        }
    }

    // Function to handle tab content display
    window.showTab = function(tabId) {
        // Hide all tab content sections
        document.querySelectorAll('.tab-content-section').forEach(section => {
            section.style.display = 'none';
        });

        // Show the selected tab content section
        document.getElementById(tabId).style.display = 'flex';
    };

    // Update price display based on radio button selection
    const subscriptionRadios = document.querySelectorAll('input[name="assinatura"]');
    const priceDisplay = document.querySelector('.price-display');

    subscriptionRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked) {
                const price = this.value;
                if (price === "19.90") {
                    priceDisplay.textContent = 'R$19,90';
                } else if (price === "179.90") {
                    priceDisplay.textContent = 'R$179,90';
                }
            }
        });
    });

    // Initialize tabs when the DOM is fully loaded
    initializeTabs();
});
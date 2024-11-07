document.addEventListener("keydown", function (event) {
    const paginationList = document.querySelector(".datatable-pagination-list");
    const firstChild = paginationList ? paginationList?.firstElementChild?.firstElementChild : null;
    const lastChild = paginationList ? paginationList?.lastElementChild?.firstElementChild : null;
    const searchInput = document.querySelector('.datatable-input[type="search"]');

    // Check if the pagination list and its children exist
    if (paginationList) {
        if (event.key === "ArrowLeft" && firstChild) {
            // Simulate a click on the first child
            firstChild.click();
        } else if (event.key === "ArrowRight" && lastChild) {
            // Simulate a click on the last child
            lastChild.click();
        }
    }

    // Check for "F" key press to focus on search input
    if (["f", "F"].includes(event.key) && searchInput) {
        // Only prevent the default action if the input is NOT focused
        if (document.activeElement !== searchInput) {
            event.preventDefault(); // Prevent typing "F" if not focused
            // Focus on the search input
            searchInput.focus();
            // Scroll the page to view the search input
            searchInput.scrollIntoView({behavior: "smooth", block: "center"});
        }
    }

    // Check for Escape key press to clear the input and Enter key to unfocus
    if (event.key === 'Escape') {
        // If the search input is focused, clear it and blur
        searchInput.value = ''; // Clear the input

        // Dispatch input event to trigger change listeners
        const event = new Event('input', {bubbles: true});
        searchInput.dispatchEvent(event);

        searchInput.blur(); // Unfocus the input
    }
    if (event.key === 'Enter') {
        // Blur the currently focused element
        document.activeElement.blur();
    }
});

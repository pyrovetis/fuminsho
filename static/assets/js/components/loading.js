// Function to remove the element with a fade-out animation
function removeLoadingContainer() {
    const loadingContainer = document.getElementById("loading-container");
    if (loadingContainer) {
        // Start the fade-out transition
        loadingContainer.style.transition = "opacity 0.5s ease";
        loadingContainer.style.opacity = "0";

        // Remove the element after the transition ends
        loadingContainer.addEventListener("transitionend", () => {
            loadingContainer.remove();
        });
    }
}

// Call the function to trigger the animation and removal
removeLoadingContainer();

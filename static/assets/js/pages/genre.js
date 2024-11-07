if (document.getElementById("table") && typeof simpleDatatables.DataTable !== 'undefined') {
    const dataTable = new simpleDatatables.DataTable("#table", {
        columns: [{select: 0, sortable: false},],
        searchable: true,
        sortable: true,
        perPage: 20,
        perPageSelect: [20, 50, 100],
    });

    // Attach reinitialization function to table events
    dataTable.on('datatable.page', reinitializeModalsAndPopovers);
    dataTable.on('datatable.update', reinitializeModalsAndPopovers);

    // Initial call to bind modals and popovers on first load
    reinitializeModalsAndPopovers();
}

// Function to reinitialize both modals and popovers
function reinitializeModalsAndPopovers() {
    // Reinitialize modals
    const modalTriggers = document.querySelectorAll('[data-modal-trigger]');
    const modalOptions = {
        placement: 'center-center',
        backdrop: 'dynamic',
        backdropClasses: 'bg-gray-900/50 dark:bg-gray-900/80 fixed inset-0 z-40 backdrop-blur-sm',
        closable: true,
    };


    for (const trigger of modalTriggers) {
        const modalId = trigger.getAttribute('data-modal-trigger');
        const modalElement = document.getElementById(modalId);
        const instanceOptions = {
            id: modalId, override: true
        };

        if (modalElement) {
            const modalInstance = new Modal(modalElement, modalOptions, instanceOptions);
            trigger.onclick = () => modalInstance.show();  // Show modal on click
        }
    }

    // Reinitialize popovers
    const popoverTriggers = document.querySelectorAll('[data-popover-trigger]');
    const popoverOptions = {
        placement: 'bottom',
        triggerType: 'hover',
        offset: 10,
    };

    for (const trigger of popoverTriggers) {
        const popoverId = trigger.getAttribute('data-popover-trigger');
        const popoverElement = document.getElementById(popoverId);
        const instanceOptions = {
            id: popoverId,
            override: true
        };

        if (popoverElement) {
            new Popover(popoverElement, trigger, popoverOptions, instanceOptions);
        }
    }
}

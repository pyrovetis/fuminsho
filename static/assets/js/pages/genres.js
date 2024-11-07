if (document.getElementById("table") && typeof simpleDatatables.DataTable !== 'undefined') {
    const dataTable = new simpleDatatables.DataTable("#table", {
        searchable: true,
        sortable: true,
        perPage: 20,
        perPageSelect: [20, 50, 100],
    });
}

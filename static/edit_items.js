document.addEventListener('DOMContentLoaded', () => {
    const groupedItemsList = document.getElementById('grouped-items-list');
    const addNewItemForm = document.getElementById('add-new-item-form');
    const newItemNameInput = document.getElementById('new-item-name');
    const newItemCategoryInput = document.getElementById('new-item-category');
    const newItemExpiringSelect = document.getElementById('new-item-expiring');
    const newItemItemNoInput = document.getElementById('new-item-item-no');
    const backToMainBtn = document.getElementById('back-to-main-btn');
    const lastEditedItemsDate = document.getElementById('last-edited-items-date');

    backToMainBtn.addEventListener('click', () => {
        window.location.href = '/';
    });

    async function loadItems() {
        try {
            const response = await fetch('/api/firstaiditems');
            console.log('[edit_items.js] Fetch response status:', response.status);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
            }
            const data = await response.json();
            const items = data.items; // Access the items array
            const lastEdited = data.last_edited; // Access the last_edited timestamp

            console.log('[edit_items.js] Fetched items:', items); // Added log
            console.log('[edit_items.js] Type of fetched items:', typeof items, 'Is Array:', Array.isArray(items));

            if (!Array.isArray(items)) {
                console.error('[edit_items.js] Fetched data is not an array:', items);
                alert('Error: Received invalid data from server.');
                return;
            }

            try {
                renderItems(items, { key: 'Item#', order: 'asc' }); // Initial sort by Item name
                populateCategoryDropdown(items);
                lastEditedItemsDate.textContent = `Last Edited: ${lastEdited || 'N/A'}`;
            } catch (renderError) {
                console.error('[edit_items.js] Error during rendering items:', renderError);
                alert('Failed to render items.');
            }
        } catch (error) {
            console.error('Error loading first aid items:', error);
            alert('Failed to load items.');
        }
    }

    function populateCategoryDropdown(items) {
        const categories = new Set();
        items.forEach(item => {
            if (item.category) {
                categories.add(item.category);
            }
        });

        // Clear existing options
        newItemCategoryInput.innerHTML = '';

        // Add a default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a category';
        newItemCategoryInput.appendChild(defaultOption);

        // Add unique categories
        Array.from(categories).sort().forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            newItemCategoryInput.appendChild(option);
        });
    }

    function sanitizeClassName(name) {
        return name
            .replace(/\s/g, '-') // Replace spaces with hyphens
            .replace(/[^a-zA-Z0-9-]/g, '-') // Replace non-alphanumeric (except hyphen) with hyphen
            .replace(/-+/g, '-') // Replace multiple hyphens with single hyphen
            .replace(/^-|-$/g, ''); // Trim leading/trailing hyphens
    }

    function renderItems(items, sortConfig = { key: 'Item#', order: 'asc' }) {
        console.log('[edit_items.js] Rendering items:', items); // Added log
        groupedItemsList.innerHTML = '';
        if (items.length === 0) {
            groupedItemsList.innerHTML = '<p>No items found.</p>';
            return;
        }

        const expandCollapseContainer = document.createElement('div');
        expandCollapseContainer.classList.add('expand-collapse-buttons');
        expandCollapseContainer.innerHTML = `
            <a href="#" id="expand-all-edit">Expand All</a>
            <a href="#" id="collapse-all-edit">Collapse All</a>
        `;
        groupedItemsList.appendChild(expandCollapseContainer);

        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th data-sort="Item#">Item# ${sortConfig.key === 'Item#' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th data-sort="Item">Item Name ${sortConfig.key === 'Item' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th data-sort="category">Category ${sortConfig.key === 'category' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th data-sort="Expiring">Expiring ${sortConfig.key === 'Expiring' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;
        const tbody = table.querySelector('tbody');

        const grouped = items.reduce((acc, item) => {
            const category = item.category || 'Uncategorized';
            if (!acc[category]) {
                acc[category] = [];
            }
            acc[category].push(item);
            return acc;
        }, {});

        const sortedCategories = Object.keys(grouped).sort((a, b) => {
            const aHasExpiring = grouped[a].some(item => item.Expiring === 'Yes');
            const bHasExpiring = grouped[b].some(item => item.Expiring === 'Yes');
            if (aHasExpiring && !bHasExpiring) return -1;
            if (!aHasExpiring && bHasExpiring) return 1;
            return a.localeCompare(b);
        });

        sortedCategories.forEach(category => {
            const categoryRow = document.createElement('tr');
            categoryRow.classList.add('category-row');
            categoryRow.dataset.category = category;
            categoryRow.innerHTML = `<td colspan="4">${category.replace('*', '')}</td>`;
            tbody.appendChild(categoryRow);

            const categoryItems = sortItems(grouped[category], sortConfig); // Sort items within each category
            categoryItems.forEach(item => {
                console.log('[edit_items.js] Processing item:', item);
                const row = document.createElement('tr');
                row.classList.add('item-row', `category-${sanitizeClassName(category)}`);
                row.innerHTML = `
                    <td>${item['Item#'] || ''}</td>
                    <td>${item.Item}</td>
                    <td>${item.category || 'Uncategorized'}</td>
                    <td>${item.Expiring || ''}</td>
                    <td>
                        <button class="delete-item-btn" data-item-name="${item.Item}">Delete</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        });

        groupedItemsList.appendChild(table);

        document.getElementById('expand-all-edit').addEventListener('click', () => {
            tbody.querySelectorAll('.item-row').forEach(row => row.style.display = '');
            tbody.querySelectorAll('.category-row').forEach(row => row.classList.remove('collapsed'));
        });

        document.getElementById('collapse-all-edit').addEventListener('click', () => {
            tbody.querySelectorAll('.item-row').forEach(row => row.style.display = 'none');
            tbody.querySelectorAll('.category-row').forEach(row => row.classList.add('collapsed'));
        });

        tbody.querySelectorAll('.category-row').forEach(row => {
            row.addEventListener('click', () => {
                const category = row.dataset.category;
                row.classList.toggle('collapsed');
                tbody.querySelectorAll(`.item-row.category-${sanitizeClassName(category)}`).forEach(itemRow => {
                    itemRow.style.display = itemRow.style.display === 'none' ? '' : 'none';
                });
            });
        });

        document.querySelectorAll('.delete-item-btn').forEach(button => {
            button.addEventListener('click', handleDeleteItem);
        });

        // Add sorting event listeners for Edit Items view
        table.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', (event) => {
                const sortKey = th.dataset.sort;
                if (sortConfig.key === sortKey) {
                    sortConfig.order = sortConfig.order === 'asc' ? 'desc' : 'asc';
                } else {
                    sortConfig.key = sortKey;
                    sortConfig.order = 'asc';
                }
                // Re-render items with new sort configuration
                renderItems(items, sortConfig);
            });
        });
    }

    // Helper function to sort items for Edit Items view
    function sortItems(items, sortConfig) {
        return [...items].sort((a, b) => {
            const valA = a[sortConfig.key];
            const valB = b[sortConfig.key];

            if (sortConfig.key === 'Item#') {
                const numA = parseInt(valA, 10);
                const numB = parseInt(valB, 10);
                return sortConfig.order === 'asc' ? numA - numB : numB - numA;
            } else if (typeof valA === 'string') {
                return sortConfig.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else {
                return sortConfig.order === 'asc' ? valA - valB : valB - valA;
            }
        });
    }

    async function handleDeleteItem(event) {
        const itemName = event.target.dataset.itemName;
        if (!confirm(`Are you sure you want to delete ${itemName}?`)) return;

        try {
            const response = await fetch(`/api/firstaiditems/${itemName}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                alert('Item deleted successfully!');
                loadItems();
            } else {
                const errorData = await response.json();
                alert(`Failed to delete item: ${errorData.detail || response.statusText}`);
            }
        } catch (error) {
            console.error('Error deleting item:', error);
            alert('Failed to delete item.');
        }
    }

    addNewItemForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const newItem = {
            "Item#": newItemItemNoInput.value,
            Item: newItemNameInput.value,
            category: newItemCategoryInput.value,
            Expiring: newItemExpiringSelect.value
        };

        try {
            const response = await fetch('/api/firstaiditems', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newItem)
            });
            if (response.ok) {
                alert('Item added successfully!');
                addNewItemForm.reset();
                loadItems();
            } else {
                const errorData = await response.json();
                alert(`Failed to add item: ${errorData.detail || response.statusText}`);
            }
        } catch (error) {
            console.error('Error adding item:', error);
            alert('Failed to add item.');
        }
    });

    loadItems();
});
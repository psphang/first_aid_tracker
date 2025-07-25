document.addEventListener('DOMContentLoaded', () => {
    
    // --- DOM Elements ---
    const kitSelectionView = document.getElementById('kit-selection-view');
    const kitManagementView = document.getElementById('kit-management-view');
    const allItemsView = document.getElementById('all-items-view');
    const kitIdInput = document.getElementById('kit-id-input');
    const enterKitBtn = document.getElementById('enter-kit-btn');
    const kitTitle = document.getElementById('kit-title');
    const switchKitBtn = document.getElementById('switch-kit-btn');
    const itemList = document.getElementById('item-list');
    const allItemsList = document.getElementById('all-items-list');
    const viewAllItemsBtn = document.getElementById('view-all-items-btn');
    const backToKitSelectionBtn = document.getElementById('back-to-kit-selection-btn');
    const addItemForm = document.getElementById('add-item-form');
    const itemSelect = document.getElementById('item-select');
    const expiryDateContainer = document.getElementById('expiry-date-container');
    const expiryDateInput = document.getElementById('expiry-date-input');
    const quantityContainer = document.getElementById('quantity-container');
    const quantityInput = document.getElementById('quantity-input');
    const editFirstAidItemsBtn = document.getElementById('edit-first-aid-items-btn');
    const lastEditedDate = document.getElementById('last-edited-date');

    let currentKitId = null;
    let firstAidItems = [];

    // --- Event Listeners ---
    enterKitBtn.addEventListener('click', enterKit);
    kitIdInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') enterKit();
    });
    switchKitBtn.addEventListener('click', () => {
        window.location.href = '/';
    });
    addItemForm.addEventListener('submit', addItem);
    viewAllItemsBtn.addEventListener('click', loadAllItems);
    backToKitSelectionBtn.addEventListener('click', () => showView('kit-selection'));
    itemSelect.addEventListener('change', handleItemSelection);
    editFirstAidItemsBtn.addEventListener('click', () => {
        window.location.href = '/edit_items';
    });

    // --- Functions ---
    function showView(viewName) {
        console.log(`Showing view: ${viewName}`);
        kitSelectionView.style.display = 'none';
        kitManagementView.style.display = 'none';
        allItemsView.style.display = 'none';

        if (viewName === 'kit-management') {
            kitManagementView.style.display = 'flex';
        } else if (viewName === 'all-items') {
            allItemsView.style.display = 'block';
        } else {
            kitSelectionView.style.display = 'flex';
        }
    }

    async function enterKit() {
        const kitId = kitIdInput.value.trim();
        if (!kitId) {
            alert('Please enter a Kit Box Code.');
            return;
        }
        window.location.href = `/kit/${kitId}`;
    }

    async function loadFirstAidItems() {
        console.log('Attempting to load first aid items...');
        try {
            const response = await fetch('/api/firstaiditems');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            firstAidItems = data.items; // Extract the items array
            console.log('First aid items loaded:', firstAidItems);
            populateItemSelect();
        } catch (error) {
            console.error('Error loading first aid items:', error);
        }
    }

    function populateItemSelect() {
        console.log('populateItemSelect: firstAidItems =', firstAidItems);
        itemSelect.innerHTML = '<option value="">Select an item</option>';

        const groupedItems = firstAidItems.reduce((acc, item) => {
            const category = item.category || 'Uncategorized';
            if (!acc[category]) {
                acc[category] = [];
            }
            acc[category].push(item);
            return acc;
        }, {});

        const sortedCategories = Object.keys(groupedItems).sort();

        sortedCategories.forEach(category => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = category;

            const sortedCategoryItems = [...groupedItems[category]].sort((a, b) => {
                const itemNoA = parseInt(a['Item#'], 10);
                const itemNoB = parseInt(b['Item#'], 10);
                return itemNoA - itemNoB;
            });

            sortedCategoryItems.forEach(item => {
                const option = document.createElement('option');
                option.value = item.Item;
                option.textContent = `${item['Item#']} ${item.Item}`;
                option.dataset.expiring = item.Expiring;
                option.dataset.itemNo = item['Item#'];
                optgroup.appendChild(option);
            });
            itemSelect.appendChild(optgroup);
        });
    }

    function sanitizeClassName(name) {
        return name
            .replace(/\s/g, '-') // Replace spaces with hyphens
            .replace(/[^a-zA-Z0-9-]/g, '-') // Replace non-alphanumeric (except hyphen) with hyphen
            .replace(/-+/g, '-') // Replace multiple hyphens with single hyphen
            .replace(/^-|-$/g, ''); // Trim leading/trailing hyphens
    }

    function handleItemSelection() {
        const selectedOption = itemSelect.options[itemSelect.selectedIndex];
        if (!selectedOption.value) {
            expiryDateContainer.style.display = 'none';
            return;
        }

        const isExpiring = selectedOption.dataset.expiring === 'Yes';
        expiryDateContainer.style.display = isExpiring ? 'block' : 'none';
    }

    async function loadItems() {
        console.log(`Attempting to load items for kit: ${currentKitId}`);
        if (!currentKitId) return;
        try {
            const response = await fetch(`/api/kits/${currentKitId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const kitData = await response.json();
            console.log('Kit data loaded:', kitData);
            renderItems(kitData.items);
            lastEditedDate.textContent = `Last Edited: ${kitData.last_edited || 'N/A'}`;
        } catch (error) {
            console.error('Error loading items:', error);
        }
    }

    function renderItems(groupedItems, sortConfig = { key: 'expiry_date', order: 'asc' }) {
        console.log('renderItems received groupedItems:', groupedItems);
        itemList.innerHTML = '';
        if (Object.keys(groupedItems).length === 0) {
            itemList.innerHTML = '<p>This kit is empty.</p>';
            return;
        }

        const expandCollapseContainer = document.createElement('div');
        expandCollapseContainer.classList.add('expand-collapse-buttons');
        expandCollapseContainer.innerHTML = `
            <a href="#" id="expand-all-kit">Expand All</a>
            <a href="#" id="collapse-all-kit">Collapse All</a>
        `;
        itemList.appendChild(expandCollapseContainer);

        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>No.</th>
                    <th data-sort="item_no">Item# ${sortConfig.key === 'item_no' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th data-sort="name">Item Name ${sortConfig.key === 'name' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th data-sort="expiry_date">Expiry Date ${sortConfig.key === 'expiry_date' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th class="qty-column" data-sort="qty">Qty ${sortConfig.key === 'qty' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th>Status</th>
                    <th>Remove</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;
        const tbody = table.querySelector('tbody');
        let itemCounter = 0;

        console.log('Categories in groupedItems:', Object.keys(groupedItems));
        const sortedCategories = Object.keys(groupedItems).sort((a, b) => {
            const aHasExpiring = groupedItems[a].some(item => item.Expiring === 'Yes');
            const bHasExpiring = groupedItems[b].some(item => item.Expiring === 'Yes');
            if (aHasExpiring && !bHasExpiring) return -1;
            if (!aHasExpiring && bHasExpiring) return 1;
            return a.localeCompare(b);
        });

        for (const category of sortedCategories) {
            const categoryRow = document.createElement('tr');
            categoryRow.classList.add('category-row');
            categoryRow.dataset.category = category;
            categoryRow.innerHTML = `<td colspan="7">${category}</td>`;
            tbody.appendChild(categoryRow);

            const items = groupedItems[category];
            items.forEach((item) => {
                itemCounter++;
                const row = document.createElement('tr');
                const sanitizedCategory = sanitizeClassName(category);
                row.classList.add(`item-row`, `category-${sanitizedCategory}`);
                const statusClass = `status-${item.status.toLowerCase().replace(' ', '-')}`;
                row.innerHTML = `
                    <td>${itemCounter}</td>
                    <td>${item.item_no || ''}</td>
                    <td>${item.name}</td>
                    <td>${item.expiry_date || ''}</td>
                    <td class="qty-column">
                        <div class="qty-controls">
                            <button class="qty-btn" data-item-id="${item.id}" data-action="decrement">-</button>
                            <input type="number" class="qty-input" data-item-id="${item.id}" value="${item.qty}" min="0">
                            <button class="qty-btn" data-item-id="${item.id}" data-action="increment">+</button>
                        </div>
                    </td>
                    <td><span class="item-status ${statusClass}">${item.status}</span></td>
                    <td><button class="remove-item-btn" data-item-id="${item.id}">✖</button></td>
                `;
                tbody.appendChild(row);
            });
        }

        itemList.appendChild(table);

        // Add event listeners
        document.getElementById('expand-all-kit').addEventListener('click', () => {
            tbody.querySelectorAll('.item-row').forEach(row => row.style.display = '');
            tbody.querySelectorAll('.category-row').forEach(row => row.classList.remove('collapsed'));
        });

        document.getElementById('collapse-all-kit').addEventListener('click', () => {
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

        document.querySelectorAll('.qty-btn').forEach(btn => {
            btn.addEventListener('click', handleQtyChange);
        });
        document.querySelectorAll('.qty-input').forEach(input => {
            input.addEventListener('change', handleQtyInputChange);
        });
        document.querySelectorAll('.remove-item-btn').forEach(btn => {
            btn.addEventListener('click', (e) => removeItem(e.target.dataset.itemId));
        });

        // Add sorting event listeners for Kit ID view
        itemList.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', (event) => {
                const sortKey = th.dataset.sort;
                if (sortConfig.key === sortKey) {
                    sortConfig.order = sortConfig.order === 'asc' ? 'desc' : 'asc';
                } else {
                    sortConfig.key = sortKey;
                    sortConfig.order = 'asc';
                }
                // Re-render items with new sort configuration
                const currentItems = Object.values(groupedItems).flat(); // Flatten grouped items for sorting
                renderItems(groupAndSortItems(currentItems, sortConfig), sortConfig);
            });
        });
    }

    // Helper function to group and sort items for Kit ID view
    function groupAndSortItems(items, sortConfig) {
        const sortedItems = [...items].sort((a, b) => {
            const valA = a[sortConfig.key];
            const valB = b[sortConfig.key];

            if (sortConfig.key === 'expiry_date') {
                if (!valA) return 1;
                if (!valB) return -1;
                return sortConfig.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else if (sortConfig.key === 'item_no') {
                const numA = parseInt(valA, 10);
                const numB = parseInt(valB, 10);
                return sortConfig.order === 'asc' ? numA - numB : numB - numA;
            } else if (typeof valA === 'string') {
                return sortConfig.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else {
                return sortConfig.order === 'asc' ? valA - valB : valB - valA;
            }
        });

        const grouped = {};
        sortedItems.forEach(item => {
            const category = item.category || 'Uncategorized';
            if (!grouped[category]) {
                grouped[category] = [];
            }
            grouped[category].push(item);
        });
        return grouped;
    }

    async function addItem(e) {
        e.preventDefault();
        const selectedOption = itemSelect.options[itemSelect.selectedIndex];
        if (!selectedOption.value) {
            alert('Please select an item.');
            return;
        }

        const name = selectedOption.value;
        const isExpiring = selectedOption.dataset.expiring === 'Yes';
        const item_no = selectedOption.dataset.itemNo;
        const expiry_date = isExpiring ? expiryDateInput.value : null;
        const qty = parseInt(quantityInput.value, 10);

        if (isExpiring && !expiry_date) {
            alert('Please provide an expiry date.');
            return;
        }
        if (isNaN(qty) || qty < 1) {
            alert('Please enter a valid quantity.');
            return;
        }

        const newItem = {
            id: `item-${Date.now()}`, // Simple unique ID
            name,
            item_no,
            expiry_date,
            qty
        };

        try {
            const response = await fetch(`/api/kits/${currentKitId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newItem)
            });

            if (!response.ok) {
                throw new Error('Failed to add item');
            }

            await loadItems(); // Reload the list
            addItemForm.reset(); // Reset the form
            expiryDateContainer.style.display = 'none'; // Hide expiry date field

        } catch (error) {
            console.error('Error adding item:', error);
            alert('Could not add item. Please try again.');
        }
    }

    function handleQtyChange(e) {
        const itemId = e.target.dataset.itemId;
        const action = e.target.dataset.action;
        const input = document.querySelector(`.qty-input[data-item-id="${itemId}"]`);
        let currentQty = parseInt(input.value, 10);

        if (action === 'increment') {
            currentQty++;
        } else if (action === 'decrement' && currentQty > 0) {
            currentQty--;
        }

        if (currentQty === 0) {
            if (confirm('Set quantity to 0? This will mark the item as Empty. To remove it completely, use the Remove button.')) {
                input.value = 0;
                updateItemQuantity(itemId, 0);
            }
        } else {
            input.value = currentQty;
            updateItemQuantity(itemId, currentQty);
        }
    }

    function handleQtyInputChange(e) {
        const itemId = e.target.dataset.itemId;
        const newQty = parseInt(e.target.value, 10);
        if (!isNaN(newQty) && newQty >= 0) {
            if (newQty === 0) {
                if (confirm('Set quantity to 0? This will mark the item as Empty. To remove it completely, use the Remove button.')) {
                    updateItemQuantity(itemId, 0);
                } else {
                    loadItems(); // Revert
                }
            } else {
                updateItemQuantity(itemId, newQty);
            }
        } else {
            loadItems(); // Revert on invalid input
        }
    }

    async function updateItemQuantity(itemId, qty) {
        try {
            const response = await fetch(`/api/kits/${currentKitId}/${itemId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ qty })
            });
            if (!response.ok) {
                throw new Error('Failed to update quantity');
            }
            await loadItems();
        } catch (error) {
            console.error('Error updating quantity:', error);
            alert('Could not update quantity. Please try again.');
            loadItems();
        }
    }

    async function removeItem(itemId) {
        if (!confirm('Are you sure you want to permanently remove this item?')) return;

        try {
            await fetch(`/api/kits/${currentKitId}/${itemId}`, { method: 'DELETE' });
            await loadItems();
        } catch (error) {
            console.error('Error removing item:', error);
        }
    }

    async function loadAllItems() {
        console.log('loadAllItems function called.');
        try {
            const response = await fetch('/api/all_items');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const allItems = await response.json();
            console.log('API response for all items:', allItems);
            // Check if allItems is an object (grouped data) or an array (flat data)
            if (Array.isArray(allItems)) {
                console.error('Expected grouped data for all items, but received an array.', allItems);
                // If it's still an array, we need to group it here for rendering
                const grouped = allItems.reduce((acc, item) => {
                    const category = item.category || 'Uncategorized';
                    if (!acc[category]) {
                        acc[category] = [];
                    }
                    acc[category].push(item);
                    return acc;
                }, {});
                renderAllItems(grouped);
            } else {
                renderAllItems(allItems);
            }
            showView('all-items');
        } catch (error) {
            console.error('Error loading all items:', error);
            alert('Failed to load all items. Check console for details.');
        }
    }

    function renderAllItems(groupedItems, sortConfig = { key: 'expiry_date', order: 'asc' }) {
        console.log('renderAllItems: received groupedItems:', groupedItems);
        allItemsList.innerHTML = '';
        if (Object.keys(groupedItems).length === 0) {
            allItemsList.innerHTML = '<p>No items found across all kits.</p>';
            return;
        }

        const expandCollapseContainer = document.createElement('div');
        expandCollapseContainer.classList.add('expand-collapse-buttons');
        expandCollapseContainer.innerHTML = `
            <a href="#" id="expand-all-all-items">Expand All</a>
            <a href="#" id="collapse-all-all-items">Collapse All</a>
        `;
        allItemsList.appendChild(expandCollapseContainer);

        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>No.</th>
                    <th data-sort="item_no">Item# ${sortConfig.key === 'item_no' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th data-sort="kit_id">Kit ID ${sortConfig.key === 'kit_id' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th data-sort="name">Item Name ${sortConfig.key === 'name' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th data-sort="expiry_date">Expiry Date ${sortConfig.key === 'expiry_date' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th class="qty-column-view" data-sort="qty">Qty ${sortConfig.key === 'qty' ? (sortConfig.order === 'asc' ? '▲' : '▼') : ''}</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;
        const tbody = table.querySelector('tbody');
        let itemCounter = 0;

        const sortedCategories = Object.keys(groupedItems).sort((a, b) => {
            const aHasExpiring = groupedItems[a].some(item => item.Expiring === 'Yes');
            const bHasExpiring = groupedItems[b].some(item => item.Expiring === 'Yes');
            if (aHasExpiring && !bHasExpiring) return -1;
            if (!aHasExpiring && bHasExpiring) return 1;
            return a.localeCompare(b);
        });

        sortedCategories.forEach(category => {
            console.log('renderAllItems: Processing category:', category);
            const categoryRow = document.createElement('tr');
            categoryRow.classList.add('category-row');
            categoryRow.dataset.category = category;
            categoryRow.innerHTML = `<td colspan="7">${category}</td>`;
            tbody.appendChild(categoryRow);

            const categoryItems = groupedItems[category];
            const sortedCategoryItems = [...categoryItems].sort((a, b) => {
                const valA = a[sortConfig.key];
                const valB = b[sortConfig.key];

                if (sortConfig.key === 'item_no') {
                    const numA = parseInt(valA, 10);
                    const numB = parseInt(valB, 10);
                    return sortConfig.order === 'asc' ? numA - numB : numB - numA;
                } else if (sortConfig.key === 'expiry_date') {
                    if (!valA) return 1;
                    if (!valB) return -1;
                    return sortConfig.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
                } else if (typeof valA === 'string') {
                    return sortConfig.order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
                } else {
                    return sortConfig.order === 'asc' ? valA - valB : valB - valA;
                }
            });

            sortedCategoryItems.forEach((item) => {
                itemCounter++;
                const row = document.createElement('tr');
                const sanitizedCategory = sanitizeClassName(category);
                row.classList.add(`item-row`, `category-${sanitizedCategory}`);
                const statusClass = `status-${item.status.toLowerCase().replace(' ', '-')}`;
                row.innerHTML = `
                    <td>${itemCounter}</td>
                    <td>${item.item_no || ''}</td>
                    <td>${item.kit_id}</td>
                    <td>${item.name}</td>
                    <td>${item.expiry_date || ''}</td>
                    <td>${item.qty}</td>
                    <td><span class="item-status ${statusClass}">${item.status}</span></td>
                `;
                tbody.appendChild(row);
            });
        });

        allItemsList.appendChild(table);

        document.getElementById('expand-all-all-items').addEventListener('click', () => {
            tbody.querySelectorAll('.item-row').forEach(row => row.style.display = '');
            tbody.querySelectorAll('.category-row').forEach(row => row.classList.remove('collapsed'));
        });

        document.getElementById('collapse-all-all-items').addEventListener('click', () => {
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

        allItemsList.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', (event) => {
                const sortKey = th.dataset.sort;
                if (sortConfig.key === sortKey) {
                    sortConfig.order = sortConfig.order === 'asc' ? 'desc' : 'asc';
                } else {
                    sortConfig.key = sortKey;
                    sortConfig.order = 'asc';
                }
                renderAllItems(groupedItems, sortConfig); // Pass groupedItems directly
            });
        });
    }

    // --- Initial State ---
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length >= 3 && pathParts[1] === 'kit' && pathParts[2]) {
        currentKitId = pathParts[2];
        kitTitle.textContent = `Kit: ${currentKitId}`;
        loadFirstAidItems();
        loadItems();
        showView('kit-management');
    } else {
        showView('kit-selection');
    }
});
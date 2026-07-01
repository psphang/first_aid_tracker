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

    // Recent items modal elements
    const recentModal = document.getElementById('recent-modal');
    const closeRecentModal = document.getElementById('close-recent-modal');
    const recentItemsList = document.getElementById('recent-items-list');

    // Edit modal elements
    const editModal = document.getElementById('edit-modal');
    const editItemForm = document.getElementById('edit-item-form');
    const editItemId = document.getElementById('edit-item-id');
    const editItemName = document.getElementById('edit-item-name');
    const editItemQty = document.getElementById('edit-item-qty');
    const editItemExpiry = document.getElementById('edit-item-expiry');
    const closeEditModal = document.getElementById('close-edit-modal');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');

    // Delete modal elements
    const deleteModal = document.getElementById('delete-modal');
    const deleteItemName = document.getElementById('delete-item-name');
    const closeDeleteModal = document.getElementById('close-delete-modal');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');

    let currentKitId = null;
    let firstAidItems = [];
    let deleteTargetId = null;
    let allKitItems = [];

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

    // Recent items modal listeners
    closeRecentModal.addEventListener('click', () => recentModal.classList.add('hidden'));
    recentModal.addEventListener('click', (e) => {
        if (e.target === recentModal) recentModal.classList.add('hidden');
    });

    // Edit modal listeners
    closeEditModal.addEventListener('click', () => editModal.classList.add('hidden'));
    cancelEditBtn.addEventListener('click', () => editModal.classList.add('hidden'));
    editItemForm.addEventListener('submit', handleEditSubmit);

    // Delete modal listeners
    closeDeleteModal.addEventListener('click', () => deleteModal.classList.add('hidden'));
    cancelDeleteBtn.addEventListener('click', () => deleteModal.classList.add('hidden'));
    confirmDeleteBtn.addEventListener('click', handleConfirmDelete);

    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.item-menu-container')) {
            document.querySelectorAll('.item-dropdown.show').forEach(d => d.classList.remove('show'));
        }
    });

    // Close modals on background click
    editModal.addEventListener('click', (e) => {
        if (e.target === editModal) editModal.classList.add('hidden');
    });
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) deleteModal.classList.add('hidden');
    });

    // --- Functions ---
    function showView(viewName) {
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
        try {
            const response = await fetch('/api/firstaiditems');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            firstAidItems = data.items;
            populateItemSelect();
        } catch (error) {
            console.error('Error loading first aid items:', error);
        }
    }

    function populateItemSelect() {
        itemSelect.innerHTML = '<option value="">Select an item</option>';
        const groupedItems = firstAidItems.reduce((acc, item) => {
            const category = item.category || 'Uncategorized';
            if (!acc[category]) acc[category] = [];
            acc[category].push(item);
            return acc;
        }, {});
        const sortedCategories = Object.keys(groupedItems).sort();
        sortedCategories.forEach(category => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = category;
            const sortedCategoryItems = [...groupedItems[category]].sort((a, b) => {
                return parseInt(a['Item#'], 10) - parseInt(b['Item#'], 10);
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
            .replace(/\s/g, '-')
            .replace(/[^a-zA-Z0-9-]/g, '-')
            .replace(/-+/g, '-')
            .replace(/^-|-$/g, '');
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
        if (!currentKitId) return;
        try {
            const response = await fetch(`/api/kits/${currentKitId}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const kitData = await response.json();
            allKitItems = [];
            Object.values(kitData.items).forEach(items => allKitItems.push(...items));
            renderItems(kitData.items);
            showRecentBanner(allKitItems);
            if (kitData.last_edited) {
                const date = new Date(kitData.last_edited);
                lastEditedDate.innerHTML = `Last Edited: ${date.toLocaleDateString()} ${date.toLocaleTimeString()} <a href="#" id="show-recent-btn">(view recent changes)</a>`;
                document.getElementById('show-recent-btn').addEventListener('click', (e) => {
                    e.preventDefault();
                    toggleRecentPanel();
                });
            } else {
                lastEditedDate.textContent = `Last Edited: N/A`;
            }
        } catch (error) {
            console.error('Error loading items:', error);
        }
    }

    function showRecentBanner(items) {
        const now = new Date();
        const recentItems = items.filter(item => {
            if (!item.updated_at) return false;
            const updated = new Date(item.updated_at);
            const hoursSince = (now - updated) / (1000 * 60 * 60);
            return hoursSince < 24;
        });

        if (recentItems.length > 0) {
            renderRecentItems(recentItems);
        }
    }

    function renderRecentItems(items) {
        recentItemsList.innerHTML = '';
        const now = new Date();
        const sorted = [...items].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
        sorted.forEach(item => {
            const div = document.createElement('div');
            div.classList.add('recent-item');
            const updated = new Date(item.updated_at);
            const timeAgo = getTimeAgo(now, updated);
            div.innerHTML = `
                <span class="recent-item-name">${item.name} (Qty: ${item.qty})</span>
                <span class="recent-item-time">${timeAgo}</span>
            `;
            recentItemsList.appendChild(div);
        });
    }

    function getTimeAgo(now, past) {
        const diffMs = now - past;
        const diffMin = Math.floor(diffMs / 60000);
        if (diffMin < 1) return 'just now';
        if (diffMin < 60) return `${diffMin} min ago`;
        const diffHr = Math.floor(diffMin / 60);
        if (diffHr < 24) return `${diffHr} hr${diffHr > 1 ? 's' : ''} ago`;
        const diffDay = Math.floor(diffHr / 24);
        return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
    }

    function toggleRecentPanel() {
        recentModal.classList.remove('hidden');
    }

    function renderItems(groupedItems, sortConfig = { key: 'expiry_date', order: 'asc' }) {
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
                    <th class="action-column">Actions</th>
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
                        <span class="qty-display">${item.qty}</span>
                    </td>
                    <td><span class="item-status ${statusClass}">${item.status}</span></td>
                    <td>
                        <div class="item-menu-container">
                            <button class="item-menu-btn" data-item-id="${item.id}" data-item-name="${item.name}">⋮</button>
                            <div class="item-dropdown" data-item-id="${item.id}">
                                <button class="btn-edit-dropdown" data-item-id="${item.id}" data-item-name="${item.name}" data-item-qty="${item.qty}" data-item-expiry="${item.expiry_date || ''}">Edit</button>
                                <button class="btn-delete-dropdown" data-item-id="${item.id}" data-item-name="${item.name}">Delete</button>
                            </div>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        itemList.appendChild(table);

        // Expand/Collapse listeners
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

        // 3-dot menu toggle
        document.querySelectorAll('.item-menu-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dropdown = btn.nextElementSibling;
                document.querySelectorAll('.item-dropdown.show').forEach(d => {
                    if (d !== dropdown) d.classList.remove('show');
                });
                dropdown.classList.toggle('show');
            });
        });

        // Edit dropdown click
        document.querySelectorAll('.btn-edit-dropdown').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                btn.closest('.item-dropdown').classList.remove('show');
                openEditModal(btn.dataset.itemId, btn.dataset.itemName, btn.dataset.itemQty, btn.dataset.itemExpiry);
            });
        });

        // Delete dropdown click
        document.querySelectorAll('.btn-delete-dropdown').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                btn.closest('.item-dropdown').classList.remove('show');
                openDeleteModal(btn.dataset.itemId, btn.dataset.itemName);
            });
        });

        // Sorting
        itemList.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', (event) => {
                const sortKey = th.dataset.sort;
                if (sortConfig.key === sortKey) {
                    sortConfig.order = sortConfig.order === 'asc' ? 'desc' : 'asc';
                } else {
                    sortConfig.key = sortKey;
                    sortConfig.order = 'asc';
                }
                const currentItems = Object.values(groupedItems).flat();
                renderItems(groupAndSortItems(currentItems, sortConfig), sortConfig);
            });
        });
    }

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
            if (!grouped[category]) grouped[category] = [];
            grouped[category].push(item);
        });
        return grouped;
    }

    // --- Edit Modal ---
    function openEditModal(itemId, itemName, qty, expiryDate) {
        editItemId.value = itemId;
        editItemName.value = itemName;
        editItemQty.value = qty;
        if (expiryDate) {
            editItemExpiry.value = expiryDate;
            editItemExpiry.disabled = false;
            editItemExpiry.parentElement.style.display = 'block';
        } else {
            editItemExpiry.value = '';
            editItemExpiry.disabled = true;
            editItemExpiry.parentElement.style.display = 'none';
        }
        editModal.classList.remove('hidden');
    }

    async function handleEditSubmit(e) {
        e.preventDefault();
        const itemId = editItemId.value;
        const newQty = parseInt(editItemQty.value, 10);
        const newExpiry = editItemExpiry.value || null;

        try {
            const response = await fetch(`/api/kits/${currentKitId}/${itemId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ qty: newQty, expiry_date: newExpiry })
            });
            if (!response.ok) throw new Error('Failed to update item');
            editModal.classList.add('hidden');
            await loadItems();
        } catch (error) {
            console.error('Error updating item:', error);
            alert('Could not update item. Please try again.');
        }
    }

    // --- Delete Modal ---
    function openDeleteModal(itemId, itemName) {
        deleteTargetId = itemId;
        deleteItemName.textContent = `Are you sure you want to delete "${itemName}"?`;
        deleteModal.classList.remove('hidden');
    }

    async function handleConfirmDelete() {
        if (!deleteTargetId) return;
        try {
            await fetch(`/api/kits/${currentKitId}/${deleteTargetId}`, { method: 'DELETE' });
            deleteModal.classList.add('hidden');
            deleteTargetId = null;
            await loadItems();
        } catch (error) {
            console.error('Error removing item:', error);
            alert('Could not delete item. Please try again.');
        }
    }

    // --- Add Item ---
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
            id: `item-${Date.now()}`,
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
            if (!response.ok) throw new Error('Failed to add item');
            await loadItems();
            addItemForm.reset();
            expiryDateContainer.style.display = 'none';
        } catch (error) {
            console.error('Error adding item:', error);
            alert('Could not add item. Please try again.');
        }
    }

    // --- All Items View ---
    async function loadAllItems() {
        try {
            const response = await fetch('/api/all_items');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const allItems = await response.json();
            renderAllItems(allItems);
            showView('all-items');
        } catch (error) {
            console.error('Error loading all items:', error);
            alert('Failed to load all items.');
        }
    }

    function renderAllItems(groupedItems, sortConfig = { key: 'expiry_date', order: 'asc' }) {
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
                    <th data-sort="item_no">Item#</th>
                    <th data-sort="kit_id">Kit ID</th>
                    <th data-sort="name">Item Name</th>
                    <th data-sort="expiry_date">Expiry Date</th>
                    <th class="qty-column-view" data-sort="qty">Qty</th>
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
                    return sortConfig.order === 'asc' ? parseInt(valA, 10) - parseInt(valB, 10) : parseInt(valB, 10) - parseInt(valA, 10);
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

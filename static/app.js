
document.addEventListener('DOMContentLoaded', () => {
    console.log('app.js loaded and DOMContentLoaded fired');

    // --- DOM Elements ---
    const kitSelectionView = document.getElementById('kit-selection-view');
    const kitManagementView = document.getElementById('kit-management-view');
    const kitIdInput = document.getElementById('kit-id-input');
    const enterKitBtn = document.getElementById('enter-kit-btn');
    const kitTitle = document.getElementById('kit-title');
    const switchKitBtn = document.getElementById('switch-kit-btn');
    const itemList = document.getElementById('item-list');
    const itemNameInput = document.getElementById('item-name-input');
    const expiryDateInput = document.getElementById('expiry-date-input');
    const addItemBtn = document.getElementById('add-item-btn');
    const viewAllItemsBtn = document.getElementById('view-all-items-btn');
    const allItemsView = document.getElementById('all-items-view');
    const backToKitSelectionBtn = document.getElementById('back-to-kit-selection-btn');
    const allItemsList = document.getElementById('all-items-list');
    console.log('viewAllItemsBtn element:', viewAllItemsBtn);

    let currentKitId = null;

    // --- Event Listeners ---
    enterKitBtn.addEventListener('click', enterKit);
    kitIdInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') enterKit();
    });
    switchKitBtn.addEventListener('click', () => {
        window.location.href = '/'; // Go back to the root URL for kit selection
    });
    addItemBtn.addEventListener('click', addItem);
    viewAllItemsBtn.addEventListener('click', () => {
        console.log('View All Items button clicked');
        loadAllItems();
    });
    backToKitSelectionBtn.addEventListener('click', () => {
        showView('kit-selection');
    });

    // --- Functions ---
    function showView(viewName) {
        console.log('showView called with:', viewName);
        const addItemFormContainer = document.querySelector('#kit-management-view .form-container');

        // Hide all views by default
        kitSelectionView.style.display = 'none';
        kitManagementView.style.display = 'none';
        allItemsView.style.display = 'none';
        console.log('All views hidden.');

        // Disable add item form elements by default and hide the form container
        itemNameInput.disabled = true;
        expiryDateInput.disabled = true;
        addItemBtn.disabled = true;
        if (addItemFormContainer) {
            addItemFormContainer.style.display = 'none';
            console.log('Add item form container hidden and elements disabled.');
        }

        if (viewName === 'kit-management') {
            kitManagementView.style.display = 'flex';
            console.log('kit-management view shown.');
            // Enable add item form elements and show the form container
            itemNameInput.disabled = false;
            expiryDateInput.disabled = false;
            addItemBtn.disabled = false;
            if (addItemFormContainer) {
                addItemFormContainer.style.display = 'flex';
                console.log('Add item form container shown and elements enabled.');
            }
        } else if (viewName === 'all-items') {
            allItemsView.style.display = 'block';
            console.log('all-items view shown.');
        } else { // kit-selection view
            kitSelectionView.style.display = 'flex';
            console.log('kit-selection view shown.');
        }
    }

    async function enterKit() {
        console.log('enterKit function called.');
        console.log('Kit ID input value:', kitIdInput.value);
        const kitId = kitIdInput.value.trim();
        if (!kitId) {
            alert('Please enter a Kit Box Code.');
            console.log('enterKit: No Kit ID entered.');
            return;
        }
        window.location.href = `/kit/${kitId}`;
    }

    async function loadItems() {
        if (!currentKitId) {
            console.log('loadItems: currentKitId is null, returning.');
            return;
        }
        console.log('loadItems: Fetching items for kit:', currentKitId);
        try {
            const response = await fetch(`/api/kits/${currentKitId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const items = await response.json();
            console.log('loadItems: Received items:', items);
            renderItems(items);
        } catch (error) {
            console.error('Error loading items:', error);
            alert('Could not load items for this kit.');
        }
    }

    function renderItems(items) {
        console.log('renderItems: Rendering items:', items);
        itemList.innerHTML = ''; // Clear existing items

        if (items.length === 0) {
            itemList.innerHTML = '<p>This kit is empty.</p>';
            console.log('renderItems: Kit is empty.');
            return;
        }

        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>No.</th>
                    <th>Item Name</th>
                    <th>Expiry Date</th>
                    <th>Status</th>
                    <th>Remove</th> <!-- For the remove button -->
                </tr>
            </thead>
            <tbody>
            </tbody>
        `;
        const tbody = table.querySelector('tbody');

        items.sort((a, b) => new Date(a.expiry_date) - new Date(b.expiry_date));

        items.forEach((item, index) => {
            const { status, statusText } = getItemStatus(item.expiry_date);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${item.name}</td>
                <td>${item.expiry_date}</td>
                <td><span class="item-status ${status}">${statusText}</span></td>
                <td><button class="remove-item-btn" data-item-id="${item.id}">✖</button></td>
            `;
            tbody.appendChild(row);
        });

        itemList.appendChild(table);
        console.log('renderItems: Items rendered.');

        // Add event listeners to new remove buttons
        document.querySelectorAll('.remove-item-btn').forEach(btn => {
            btn.addEventListener('click', (e) => removeItem(e.target.dataset.itemId));
        });
    }

    async function addItem() {
        const name = itemNameInput.value.trim();
        const expiry_date = expiryDateInput.value;

        if (!name || !expiry_date) {
            alert('Please provide both item name and expiry date.');
            return;
        }

        const newItem = {
            id: `id_${new Date().getTime()}`,
            name,
            expiry_date
        };

        try {
            await fetch(`/api/kits/${currentKitId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newItem)
            });
            itemNameInput.value = '';
            expiryDateInput.value = '';
            await loadItems();
        } catch (error) {
            console.error('Error adding item:', error);
            alert('Could not add the item.');
        }
    }

    async function removeItem(itemId) {
        if (!confirm('Are you sure you want to remove this item?')) return;

        try {
            await fetch(`/api/kits/${currentKitId}/${itemId}`, { method: 'DELETE' });
            await loadItems();
        } catch (error) {
            console.error('Error removing item:', error);
            alert('Could not remove the item.');
        }
    }

    function getItemStatus(expiryDate) {
        const now = new Date();
        const expiry = new Date(expiryDate);
        const thirtyDaysFromNow = new Date();
        thirtyDaysFromNow.setDate(now.getDate() + 30);

        now.setHours(0, 0, 0, 0);
        expiry.setHours(0, 0, 0, 0);

        if (expiry < now) {
            return { status: 'status-expired', statusText: 'Expired' };
        } else if (expiry <= thirtyDaysFromNow) {
            return { status: 'status-soon', statusText: 'Expires Soon' };
        } else {
            return { status: 'status-ok', statusText: 'OK' };
        }
    }

    async function loadAllItems() {
        console.log('Attempting to load all items...');
        try {
            const response = await fetch('/api/all_items');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const allItems = await response.json();
            console.log('loadAllItems: Received all items:', allItems);
            renderAllItems(allItems);
            showView('all-items');
        } catch (error) {
            console.error('Error loading all items:', error);
            alert('Could not load all items.');
        }
    }

    function renderAllItems(items) {
        console.log('renderAllItems: Rendering all items:', items);
        allItemsList.innerHTML = '';

        if (items.length === 0) {
            allItemsList.innerHTML = '<p>No items found across all kits.</p>';
            console.log('renderAllItems: No items found across all kits.');
            return;
        }

        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>No.</th>
                    <th>Kit ID</th>
                    <th>Item Name</th>
                    <th>Expiry Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        `;
        const tbody = table.querySelector('tbody');

        items.sort((a, b) => new Date(a.expiry_date) - new Date(b.expiry_date));

        items.forEach((item, index) => {
            const { status, statusText } = getItemStatus(item.expiry_date);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${item.kit_id}</td>
                <td>${item.name}</td>
                <td>${item.expiry_date}</td>
                <td><span class="item-status ${status}">${statusText}</span></td>
            `;
            tbody.appendChild(row);
        });

        allItemsList.appendChild(table);
        console.log('renderAllItems: All items rendered.');
    }

    // --- Initial State ---
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length >= 3 && pathParts[1] === 'kit' && pathParts[2]) {
        currentKitId = pathParts[2];
        kitTitle.textContent = `Kit: ${currentKitId}`;
        loadItems();
        showView('kit-management');
    } else {
        showView('kit-selection');
    }
});

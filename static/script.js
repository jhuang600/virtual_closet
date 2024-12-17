document.addEventListener('DOMContentLoaded', () => {
    console.log("JavaScript is connected!");

    // event listener for the upload form submisssion
    document.getElementById('uploadForm').addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData();
        formData.append('name', document.getElementById('itemName').value);
        formData.append('category', document.getElementById('itemCategory').value);
        formData.append('color', document.getElementById('itemColor').value);
        formData.append('image', document.getElementById('itemImage').files[0]);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to upload item');
            }

            const result = await response.json();
            alert(result.message);
            loadItems();
        } catch (error) {
            console.error('Error uploading item:', error);
        }
    });

    // add an event listener for the seach form submission
    document.getElementById('searchForm').addEventListener('submit', async (event) => {
        event.preventDefault();

        // get input values from the form
        const name = document.getElementById('searchName').value;
        const category = document.getElementById('searchCategory').value;
        const color = document.getElementById('searchColor').value;

        // construct query parameters for the search request
        const params = new URLSearchParams();
        if (name) params.append('name', name);
        if (category) params.append('category', category);
        if (color) params.append('color', color);

        try {
            // send a GET request to the backend with the search parameters
            const response = await fetch(`items/search?${params.toString()}`);
            const data = await response.json();

            // display the results in the results div
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = ''; // clear any previous results

            if (data.length === 0) {
                resultsDiv.textContent = "No items found!";
            } else {
                data.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.setAttribute('id', `item-${item.id}`);
                    itemDiv.innerHTML = `
                        <strong>${item.name}</strong> - ${item.category} - ${item.color}
                        <br>
                        <img src="${item.image_url}" alt="${item.name}" width="150">
                        <button class="delete-btn" data-id="${item.id}" style="background: none; border: none; cursor: pointer;">
                            <i class="fas fa-trash" style="color: red;"></i>
                        </button>
                    `;
                    resultsDiv.appendChild(itemDiv);
                });
                // Attach delete event listeners to the dynamically added buttons
                document.querySelectorAll('.delete-btn').forEach(button => {
                    button.addEventListener('click', () => {
                        const id = button.getAttribute('data-id');
                        deleteItem(id);
                    });
                });
            }
        } catch (error) {
            console.error('Error fetching items:', error);
        }
    });

    // function to load and display all items when the page loads
    async function loadItems() {
        try {
            const response = await fetch('/items');
            const data = await response.json();

            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';

            if (data.length === 0) {
                resultsDiv.textContent = "No items found!";
            } else {
                data.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.setAttribute('id', `item-${item.id}`);
                    itemDiv.innerHTML = `
                        <strong>${item.name}</strong> - ${item.category} - ${item.color}
                        <br>
                        <img src="${item.image_url}" alt="${item.name}" width="150">
                        <button class="delete-btn" data-id="${item.id}" style="background: none; border: none; cursor: pointer;">
                            <i class="fas fa-trash" style="color: red;"></i>
                        </button>
                    `;
                    resultsDiv.appendChild(itemDiv)
                });
                // Add event listeners for delete buttons
                document.querySelectorAll('.delete-btn').forEach(button => {
                    button.addEventListener('click', () => {
                        const id = button.getAttribute('data-id');
                        deleteItem(id);
                    });
                });
            }
        } catch (error) {
            console.error('Error loading items', error);
        }
    }

    // Function to delete an item
    async function deleteItem(id) {
        try {
            const response = await fetch(`/items/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete item');
            }

            const result = await response.json();
            alert(result.message);

            // Remove the deleted item directly from the DOM
            const itemDiv = document.getElementById(`item-${id}`);
            if (itemDiv) {
                itemDiv.remove();
            }
        } catch (error) {
            console.error('Error deleting item:', error);
        }
    }

    loadItems();
});



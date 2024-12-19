let currentEditId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadItems();
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
            displayItems(data);
        } catch (error) {
            console.error('Error fetching items:', error);
        }
    });

    // Function to display items
    function displayItems(items) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = ''; // Clear previous results
    
        if (items.length === 0) {
            resultsDiv.textContent = "No items found!";
        } else {
            items.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.setAttribute('id', `item-${item.id}`);
                itemDiv.innerHTML = `
                    <strong>${item.name}</strong> - ${item.category} - ${item.color}
                    <br>
                    <img src="${item.image_url}" alt="${item.name}" width="150">
                    <br>
                    <button class="delete-btn" data-id="${item.id}" style="background: none; border: none; cursor: pointer;">
                        <i class="fas fa-trash" style="color: red;"></i>
                    </button>
                    <button class="update-btn" data-id="${item.id}" style="background: none; border: none; cursor: pointer;">
                        <i class="fas fa-edit" style="color: blue;"></i>
                    </button>
                `;
                resultsDiv.appendChild(itemDiv);
            });
    
            // Attach event listeners for delete buttons
            document.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', () => {
                    const id = button.getAttribute('data-id');
                    deleteItem(id);
                });
            });
    
            // Attach event listeners for update buttons
            document.querySelectorAll('.update-btn').forEach(button => {
                button.addEventListener('click', () => {
                    const id = button.getAttribute('data-id');
                    openUpdateForm(id); // Opens the update form
                });
            });
        }
    }
    

    // function to load and display all items when the page loads
    async function loadItems() {
        try {
            const response = await fetch('/items'); 
            const data = await response.json();    
            displayItems(data);                   
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

    // function to open the update form modal
    async function openUpdateForm(id) {
        console.log("openUpdateForm triggered for ID:", id);
        try {
            const response = await fetch(`/items/${id}`);
            if (!response.ok) throw new Error('Failed to fetch item details');

            const item = await response.json();
            console.log("Fetched item data:", item);

            // Prefill the modal form
            document.getElementById('updateName').value = item.name;
            document.getElementById('updateCategory').value = item.category;
            document.getElementById('updateColor').value = item.color;
            document.getElementById('updateImage').value = ''; 

            currentEditId = id;
            const modal = document.getElementById('updateModal');
            modal.style.display = 'block';
            console.log("Modal display style set to 'block'");
        } catch (error) {
            console.error('Error fetching item details:', error);
        }
    }

    // Function to save updates
    document.getElementById('saveUpdateBtn').addEventListener('click', async () => {
        const formData = new FormData();
        formData.append('name', document.getElementById('updateName').value);
        formData.append('category', document.getElementById('updateCategory').value);
        formData.append('color', document.getElementById('updateColor').value);

        const image = document.getElementById('updateImage').files[0];
        if (image) formData.append('image', image);

        try {
            const response = await fetch(`/items/${currentEditId}`, {
                method: 'PUT',
                body: formData
            });

            if (!response.ok) throw new Error('Failed to update item');

            const result = await response.json();
            alert(result.message);

            document.getElementById('updateModal').style.display = 'none';
            loadItems();
        } catch (error) {
            console.error('Error updating item:', error);
        }
    });

    // Close modal button
    document.getElementById('closeModalBtn').addEventListener('click', () => {
        document.getElementById('updateModal').style.display = 'none';
    });

    // Show login modal
    document.getElementById('showLoginBtn').addEventListener('click', () => {
        document.getElementById('loginModal').style.display = 'block';
    });

    // Login function
    document.getElementById('loginBtn').addEventListener('click', async () => {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                alert('Login successful');
                document.getElementById('loginModal').style.display = 'none';
                document.getElementById('logoutBtn').style.display = 'block';
                document.getElementById('showLoginBtn').style.display = 'none';
                loadItems();
            } else {
                alert('Invalid credentials');
            }
        } catch (error) {
            console.error('Error logging in: ', error);
        } 
    });

    // Logout function
    document.getElementById('logoutBtn').addEventListener('click', async () => {
        const response = await fetch('/logout');
        if (response.ok) {
            alert('Logged out');
            document.getElementById('logoutBtn').style.display = 'none';
            document.getElementById('showLoginBtn').style.display = 'block';
            document.getElementById('results').innerHTML = '';
        }
    });


    loadItems();
});



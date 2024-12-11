// Placeholder for interactivity
console.log("JavaScript is connected!");

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
                itemDiv.textContent = `${item.name} - ${item.category} - ${item.color}`;
                resultsDiv.appendChild(itemDiv);
            })
        }
    } catch (error) {
        console.error('Error fetching items:', error);
    }
});
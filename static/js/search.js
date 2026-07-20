document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('food_search_input');
    const resultsContainer = document.getElementById('food_search_results');
    const foodIdInput = document.getElementById('food_id');
    const foodNameDisplay = document.getElementById('selected_food_name');

    let activeRequest = null;

    function clearResults() {
        resultsContainer.innerHTML = '';
    }

    function renderResults(items) {
        clearResults();
        if (!items.length) {
            resultsContainer.innerHTML = '<div class="no-results">No foods found</div>';
            return;
        }

        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'search-item';
            div.innerHTML = `${item.name} <span class="small muted">(${Math.round(item.calories_per_100g)} kcal/100g)</span>`;
            if (item.is_favourite) {
                div.classList.add('favourite');
                const star = document.createElement('span');
                star.textContent = ' ★';
                star.className = 'fav-star';
                div.appendChild(star);
            }
            div.addEventListener('click', function () {
                foodIdInput.value = item.id;
                foodNameDisplay.textContent = item.name;
                clearResults();
            });
            resultsContainer.appendChild(div);
        });
    }

    let debounceTimer = null;
    searchInput.addEventListener('input', function (e) {
        const q = e.target.value.trim();
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            if (!q) {
                clearResults();
                return;
            }

            // Cancel previous request if still running
            if (activeRequest && typeof activeRequest.abort === 'function') {
                try { activeRequest.abort(); } catch (e) { /* ignore */ }
            }

            activeRequest = fetch(`/food-search?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(data => {
                    renderResults(data);
                    activeRequest = null;
                }).catch(err => {
                    // ignore network errors for now
                    activeRequest = null;
                });
        }, 200);
    });
});

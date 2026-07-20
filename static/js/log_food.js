(function () {
    const searchInput = document.getElementById('food_search');
    const foodIdInput = document.getElementById('food_id');
    const resultsBox = document.getElementById('food_results');
    const selectedLabel = document.getElementById('selected_food_label');
    const form = document.getElementById('logFoodForm');

    if (!searchInput || !foodIdInput || !resultsBox) {
        return;
    }

    let debounceTimer = null;
    let cachedFoods = [];

    function renderResults(foods) {
        resultsBox.innerHTML = '';
        if (!foods.length) {
            resultsBox.innerHTML = '<p class="food-result-empty">No foods match your search.</p>';
            resultsBox.hidden = false;
            return;
        }

        foods.forEach((food) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'food-result-item';
            const star = food.is_favourite ? '★ ' : '';
            button.textContent = `${star}${food.name} (${food.calories_per_100g} kcal / 100g)`;
            button.addEventListener('click', () => selectFood(food));
            resultsBox.appendChild(button);
        });
        resultsBox.hidden = false;
    }

    function filterCached(query) {
        const term = query.trim().toLowerCase();
        if (!term) {
            return cachedFoods.slice(0, 50);
        }
        return cachedFoods.filter((food) => food.name.toLowerCase().includes(term));
    }

    function selectFood(food) {
        foodIdInput.value = food.id;
        selectedLabel.textContent = `Selected: ${food.name}`;
        searchInput.value = food.name;
        resultsBox.hidden = true;
    }

    async function fetchFoods(query) {
        const url = `/api/foods/search?q=${encodeURIComponent(query)}`;
        const response = await fetch(url);
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        cachedFoods = data.foods || [];
        renderResults(filterCached(query));
    }

    searchInput.addEventListener('input', () => {
        const query = searchInput.value;
        foodIdInput.value = '';
        selectedLabel.textContent = 'No food selected yet.';
        window.clearTimeout(debounceTimer);
        debounceTimer = window.setTimeout(() => {
            fetchFoods(query);
        }, 250);
    });

    searchInput.addEventListener('focus', () => {
        if (!cachedFoods.length) {
            fetchFoods('');
        } else {
            renderResults(filterCached(searchInput.value));
        }
    });

    document.addEventListener('click', (event) => {
        if (!resultsBox.contains(event.target) && event.target !== searchInput) {
            resultsBox.hidden = true;
        }
    });

    form.addEventListener('submit', (event) => {
        if (!foodIdInput.value) {
            event.preventDefault();
            selectedLabel.textContent = 'Please select a food from the search results.';
        }
    });
})();

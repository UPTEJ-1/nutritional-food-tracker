(function () {
    const searchInput = document.getElementById('food_search');
    const foodIdInput = document.getElementById('food_id');
    const resultsBox = document.getElementById('food_results');
    const selectedLabel = document.getElementById('selected_food_label');
    const form = document.getElementById('logFoodForm');
    const addToListBtn = document.getElementById('addToList');
    const pendingItemsContainer = document.getElementById('pendingItems');
    const pendingSummary = document.getElementById('pendingSummary');
    const batchInput = document.getElementById('batch_entries');

    if (!searchInput || !resultsBox || !form) return;

    let debounceTimer = null;
    let cachedFoods = [];
    let selectedFood = null; // full food object
    let pending = [];

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
        if (!term) return cachedFoods.slice(0, 50);
        return cachedFoods.filter((food) => food.name.toLowerCase().includes(term));
    }

    function selectFood(food) {
        selectedFood = food;
        foodIdInput.value = food.id;
        selectedLabel.textContent = `Selected: ${food.name} (${food.calories_per_100g} kcal/100g)`;
        searchInput.value = food.name;
        resultsBox.hidden = true;
    }

    async function fetchFoods(query) {
        try {
            const url = `/api/foods/search?q=${encodeURIComponent(query)}`;
            const response = await fetch(url);
            if (!response.ok) return;
            const data = await response.json();
            cachedFoods = data.foods || [];
            renderResults(filterCached(query));
        } catch (e) {
            console.error('Error fetching foods', e);
        }
    }

    function renderPending() {
        pendingItemsContainer.innerHTML = '';
        if (!pending.length) {
            pendingItemsContainer.innerHTML = '<p class="food-result-empty">No foods in the list. Use "Add to list" to queue multiple items.</p>';
            pendingSummary.textContent = '';
            batchInput.value = '';
            return;
        }

        const ul = document.createElement('div');
        ul.style.display = 'flex';
        ul.style.flexDirection = 'column';
        ul.style.gap = '8px';

        let totalCalories = 0;

        pending.forEach((item, idx) => {
            const row = document.createElement('div');
            row.className = 'food-item';
            row.style.display = 'flex';
            row.style.justifyContent = 'space-between';
            row.style.alignItems = 'center';

            const info = document.createElement('div');
            info.className = 'food-info';
            const name = document.createElement('div');
            name.className = 'food-name';
            name.textContent = `${item.name} — ${item.quantity} g (${item.meal})`;
            const details = document.createElement('div');
            details.className = 'food-details';
            details.textContent = `${item.calories.toFixed(0)} kcal`;
            info.appendChild(name);
            info.appendChild(details);

            const actions = document.createElement('div');
            actions.className = 'food-actions';
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-secondary btn-small';
            removeBtn.textContent = 'Remove';
            removeBtn.addEventListener('click', () => {
                pending.splice(idx, 1);
                renderPending();
            });
            actions.appendChild(removeBtn);

            row.appendChild(info);
            row.appendChild(actions);
            ul.appendChild(row);

            totalCalories += item.calories;
        });

        pendingItemsContainer.appendChild(ul);
        pendingSummary.textContent = `Items: ${pending.length} — Total ≈ ${totalCalories.toFixed(0)} kcal`;
        batchInput.value = JSON.stringify(pending);
    }

    // Add current selection to pending list
    if (addToListBtn) {
        addToListBtn.addEventListener('click', () => {
            const qtyEl = document.getElementById('quantity_grams');
            const mealEl = document.getElementById('meal_type');
            const qty = parseFloat(qtyEl.value);
            const meal = mealEl.value;

            if (!selectedFood || !selectedFood.id) {
                selectedLabel.textContent = 'Please select a food from the search results.';
                return;
            }
            if (!qty || qty <= 0) {
                selectedLabel.textContent = 'Please enter a valid quantity in grams.';
                return;
            }
            if (!meal) {
                selectedLabel.textContent = 'Please select a meal type.';
                return;
            }

            // compute calories based on calories_per_100g
            const caloriesPer100 = parseFloat(selectedFood.calories_per_100g) || 0;
            const calories = (caloriesPer100 * qty) / 100.0;

            const item = {
                id: selectedFood.id,
                name: selectedFood.name,
                quantity: qty,
                meal: meal,
                calories: calories
            };

            pending.push(item);

            // Reset inputs for next entry but keep search text
            // Keep selectedFood cleared so user must re-select or search
            selectedFood = null;
            foodIdInput.value = '';
            document.getElementById('food_search').value = '';
            selectedLabel.textContent = 'No food selected yet.';
            document.getElementById('quantity_grams').value = '';
            document.getElementById('meal_type').value = '';

            renderPending();
        });
    }

    searchInput.addEventListener('input', () => {
        const query = searchInput.value;
        foodIdInput.value = '';
        selectedLabel.textContent = 'No food selected yet.';
        selectedFood = null;
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
        if (pending.length) {
            // submit pending as JSON in batch_entries. Ensure server receives it.
            batchInput.value = JSON.stringify(pending);
            // allow submit
            return;
        }

        // If no pending items, fallback to single-item validation
        if (!foodIdInput.value) {
            event.preventDefault();
            selectedLabel.textContent = 'Please select a food from the search results.';
            return;
        }

        // ensure quantity and meal are present
        const qty = document.getElementById('quantity_grams').value;
        const meal = document.getElementById('meal_type').value;
        if (!qty || !meal) {
            event.preventDefault();
            selectedLabel.textContent = 'Please enter quantity and meal type.';
        }
    });

})();

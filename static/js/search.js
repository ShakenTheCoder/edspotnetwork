document.addEventListener('DOMContentLoaded', function() {
    const userTypeSelect = document.getElementById('userTypeSelect');
    const studentFilters = document.querySelectorAll('.student-filter');
    const universityFilters = document.querySelectorAll('.university-filter');
    const searchInput = document.querySelector('input[name="q"]');
    const searchForm = document.querySelector('form[action*="/search"]');
    
    // Function to show/hide filters based on user type
    function updateFiltersVisibility() {
        const selectedValue = userTypeSelect.value;
        
        if (selectedValue === 'student') {
            studentFilters.forEach(el => el.classList.remove('d-none'));
            universityFilters.forEach(el => el.classList.add('d-none'));
        } else if (selectedValue === 'university') {
            studentFilters.forEach(el => el.classList.add('d-none'));
            universityFilters.forEach(el => el.classList.remove('d-none'));
        } else {
            // Show all for "All" option
            studentFilters.forEach(el => el.classList.remove('d-none'));
            universityFilters.forEach(el => el.classList.remove('d-none'));
        }
    }
    
    // Create a suggestions container
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'search-suggestions position-absolute w-100 mt-1 shadow rounded bg-dark';
    suggestionsContainer.style.zIndex = '1000';
    suggestionsContainer.style.display = 'none';
    
    // Add suggestions container after searchInput
    if (searchInput) {
        searchInput.parentNode.style.position = 'relative';
        searchInput.parentNode.appendChild(suggestionsContainer);
        
        // Function to fetch search suggestions
        let debounceTimer;
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            const userType = userTypeSelect.value;
            
            clearTimeout(debounceTimer);
            
            if (query.length < 2) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            debounceTimer = setTimeout(() => {
                fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}&type=${encodeURIComponent(userType)}`)
                    .then(response => response.json())
                    .then(data => {
                        suggestionsContainer.innerHTML = '';
                        
                        if (data.length === 0) {
                            suggestionsContainer.style.display = 'none';
                            return;
                        }
                        
                        data.forEach(item => {
                            const suggestionItem = document.createElement('div');
                            suggestionItem.className = 'suggestion-item p-2 border-bottom';
                            suggestionItem.innerHTML = `
                                <div class="d-flex align-items-center">
                                    <div class="me-2">
                                        <i class="fas fa-${item.type === 'student' ? 'user' : 'university'} text-${item.type === 'student' ? 'primary' : 'success'}"></i>
                                    </div>
                                    <div>
                                        <div class="fw-bold">${item.name}</div>
                                        <div class="small text-muted">${item.subtitle}</div>
                                    </div>
                                </div>
                            `;
                            
                            suggestionItem.addEventListener('click', () => {
                                searchInput.value = item.name;
                                suggestionsContainer.style.display = 'none';
                                // Set user type if not already set
                                if (!userTypeSelect.value) {
                                    userTypeSelect.value = item.type;
                                    updateFiltersVisibility();
                                }
                                // Submit form
                                searchForm.submit();
                            });
                            
                            suggestionsContainer.appendChild(suggestionItem);
                        });
                        
                        suggestionsContainer.style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Error fetching suggestions:', error);
                        suggestionsContainer.style.display = 'none';
                    });
            }, 300);
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!suggestionsContainer.contains(e.target) && e.target !== searchInput) {
                suggestionsContainer.style.display = 'none';
            }
        });
        
        // Show suggestions when focusing on search input
        searchInput.addEventListener('focus', function() {
            if (this.value.trim().length >= 2) {
                suggestionsContainer.style.display = 'block';
            }
        });
    }
    
    // Initial setup
    updateFiltersVisibility();
    
    // Listen for changes
    userTypeSelect.addEventListener('change', updateFiltersVisibility);
    
    // Add hover effect to search results
    const searchResultCards = document.querySelectorAll('.search-result-card');
    searchResultCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow-lg');
            this.style.transform = 'translateY(-5px)';
            this.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow-lg');
            this.style.transform = 'translateY(0)';
        });
    });
});
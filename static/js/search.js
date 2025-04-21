document.addEventListener('DOMContentLoaded', function() {
    const userTypeSelect = document.getElementById('userTypeSelect');
    const studentFilters = document.querySelectorAll('.student-filter');
    const universityFilters = document.querySelectorAll('.university-filter');
    
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
    
    // Initial setup
    updateFiltersVisibility();
    
    // Listen for changes
    userTypeSelect.addEventListener('change', updateFiltersVisibility);
});
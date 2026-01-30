document.addEventListener('DOMContentLoaded', () => {

    /* ---------------- GENERIC UPLOAD HANDLER ---------------- */
    function setupDropZone(zoneId, inputSelector, allowedExts) {
        const zone = document.getElementById(zoneId);
        if (!zone) return;

        // Find input inside the zone (or by ID if specific)
        const input = zone.querySelector(inputSelector) || zone.querySelector('input[type="file"]');
        const info = zone.querySelector('.file-info');

        if (!input) return;

        zone.addEventListener('click', () => input.click());

        zone.addEventListener('dragover', e => {
            e.preventDefault();
            zone.style.background = '#eef2ff';
        });

        zone.addEventListener('dragleave', () => {
            zone.style.background = '#f8fafc';
        });

        zone.addEventListener('drop', e => {
            e.preventDefault();
            zone.style.background = '#f8fafc';
            input.files = e.dataTransfer.files;
            validate(input.files[0]);
        });

        input.addEventListener('change', () => validate(input.files[0]));

        function validate(file) {
            if (!file) return;
            const ext = file.name.split('.').pop().toLowerCase();
            
            if (!allowedExts.includes(ext)) {
                info.textContent = 'Invalid file type';
                info.style.color = '#ef4444';
                input.value = ''; // Clear input
            } else {
                info.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
                info.style.color = '#10b981';
            }
        }
    }

    // Initialize Contact List Zone
    setupDropZone('drop-zone-contacts', 'input[name="file"]', ['csv', 'xlsx', 'xls']);
    
    // Initialize Resume Zone
    setupDropZone('drop-zone-resume', '#resume_input', ['pdf']);


    /* ---------------- CHECKBOXES ---------------- */
    const selectAll = document.getElementById('select-all');
    const selectedCount = document.getElementById('selected-count');

    function updateCount() {
        if (!selectedCount) return;
        selectedCount.textContent = document.querySelectorAll('.row-check:checked').length;
    }

    if (selectAll) {
        selectAll.addEventListener('change', () => {
            document.querySelectorAll('.row-check').forEach(cb => cb.checked = selectAll.checked);
            updateCount();
        });
    }

    document.addEventListener('change', e => {
        if (e.target.classList.contains('row-check')) updateCount();
    });
});
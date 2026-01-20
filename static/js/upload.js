document.addEventListener('DOMContentLoaded', () => {

    /* ---------------- UPLOAD (SAFE) ---------------- */

    const dropZone = document.getElementById('drop-zone');
    const fileInput = dropZone?.querySelector('input[type="file"]');
    const fileInfo = document.getElementById('file-info');

    if (dropZone && fileInput) {
        const allowed = ['pdf', 'csv', 'xlsx'];

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', e => {
            e.preventDefault();
            dropZone.style.background = '#eef2ff';
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.style.background = '#f8fafc';
        });

        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.style.background = '#f8fafc';
            fileInput.files = e.dataTransfer.files;
            validateFile();
        });

        fileInput.addEventListener('change', validateFile);

        function validateFile() {
            const file = fileInput.files[0];
            if (!file) return;

            const ext = file.name.split('.').pop().toLowerCase();
            if (!allowed.includes(ext)) {
                fileInfo.textContent = 'Invalid file type';
                fileInfo.style.color = '#ef4444';
                fileInput.value = '';
                return;
            }

            fileInfo.textContent =
                `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            fileInfo.style.color = '#10b981';
        }
    }

    /* ---------------- CHECKBOXES (ALWAYS ACTIVE) ---------------- */

    const selectAll = document.getElementById('select-all');
    const selectedCount = document.getElementById('selected-count');

    function updateCount() {
        if (!selectedCount) return;
        selectedCount.textContent =
            document.querySelectorAll('.row-check:checked').length;
    }

    if (selectAll) {
        selectAll.addEventListener('change', () => {
            document.querySelectorAll('.row-check').forEach(cb => {
                cb.checked = selectAll.checked;
            });
            updateCount();
        });
    }

    document.addEventListener('change', e => {
        if (e.target.classList.contains('row-check')) {
            updateCount();
        }
    });
});

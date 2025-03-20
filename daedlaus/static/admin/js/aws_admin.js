// AWS Admin JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Add functionality to test connection buttons
    const testButtons = document.querySelectorAll('.aws-test-connection');
    
    if (testButtons.length > 0) {
        testButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const url = this.getAttribute('data-url');
                const statusElement = document.querySelector(this.getAttribute('data-target'));
                
                if (!url || !statusElement) {
                    console.error('Missing URL or target element');
                    return;
                }
                
                // Show loading state
                statusElement.innerHTML = '<span>Testing connection...</span>';
                statusElement.className = 'validation-status validation-pending';
                
                // Send AJAX request
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusElement.innerHTML = `<span>✓ Success: ${data.message}</span>`;
                        statusElement.className = 'validation-status validation-success';
                    } else {
                        statusElement.innerHTML = `<span>✗ Error: ${data.message}</span>`;
                        statusElement.className = 'validation-status validation-error';
                    }
                })
                .catch(error => {
                    statusElement.innerHTML = `<span>✗ Error: ${error.message}</span>`;
                    statusElement.className = 'validation-status validation-error';
                });
            });
        });
    }
    
    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Mark AWS credential fields for special handling
    const sensitiveFields = document.querySelectorAll('input[name="aws_access_key_id"], input[name="aws_secret_access_key"]');
    sensitiveFields.forEach(field => {
        field.setAttribute('autocomplete', 'off');
        // Add a small info icon next to sensitive fields
        const helpText = document.createElement('span');
        helpText.innerHTML = ' <i class="sensitive-field-icon">🔒</i>';
        helpText.title = 'This field contains sensitive information';
        field.parentNode.appendChild(helpText);
    });
});
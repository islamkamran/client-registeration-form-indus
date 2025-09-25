document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('contactForm');
    const successModal = document.getElementById('successModal');
    const countdownElement = document.getElementById('countdown');
    
    // API endpoint - relative URL since we're serving from same domain
    const API_URL = '/api/contact';
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = {
            full_name: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            phone_number: document.getElementById('phone').value,
            preferred_contact_method: document.getElementById('contactMethod').value,
            message: document.getElementById('message').value
        };
        
        // Basic client-side validation
        if (!validateForm(formData)) {
            return;
        }
        
        // Show loading state on button
        const submitBtn = form.querySelector('.luxury-btn');
        const originalText = submitBtn.querySelector('.btn-text').textContent;
        submitBtn.querySelector('.btn-text').textContent = 'Submitting...';
        submitBtn.disabled = true;
        
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                // Show success modal
                showSuccessModal();
                // Reset form
                form.reset();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Submission failed');
            }
        } catch (error) {
            alert('Error submitting form: ' + error.message);
        } finally {
            // Reset button state
            submitBtn.querySelector('.btn-text').textContent = originalText;
            submitBtn.disabled = false;
        }
    });
    
    function validateForm(data) {
        // Basic validation
        if (!data.full_name.trim()) {
            alert('Please enter your full name');
            return false;
        }
        
        if (!data.email.trim()) {
            alert('Please enter your email address');
            return false;
        }
        
        // Simple email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(data.email)) {
            alert('Please enter a valid email address');
            return false;
        }
        
        if (!data.phone_number.trim()) {
            alert('Please enter your phone number');
            return false;
        }
        
        if (!data.preferred_contact_method) {
            alert('Please select a preferred contact method');
            return false;
        }
        
        return true;
    }
    
    function showSuccessModal() {
        successModal.style.display = 'flex';
        
        let countdown = 5;
        countdownElement.textContent = countdown;
        
        const countdownInterval = setInterval(() => {
            countdown--;
            countdownElement.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(countdownInterval);
                successModal.style.display = 'none';
                // Optionally scroll to top of form
                window.scrollTo(0, 0);
            }
        }, 1000);
    }
    
    // Close modal if clicked outside content
    successModal.addEventListener('click', function(e) {
        if (e.target === successModal) {
            successModal.style.display = 'none';
        }
    });
});
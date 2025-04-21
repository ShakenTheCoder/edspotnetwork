// Edspot JavaScript functionality

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any components that need JavaScript functionality
    initializeTooltips();
    handleLikeButtons();
    setupMessagePolling();
    setupChatPolling();
    
    // Set up navigation active states
    setActiveNavItem();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Handle post like/unlike buttons
function handleLikeButtons() {
    const likeButtons = document.querySelectorAll('.like-button');
    
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const postId = this.dataset.postId;
            const action = this.dataset.action; // 'like' or 'unlike'
            const url = `/post/${action}/${postId}`;
            
            // Send AJAX request to like/unlike post
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update the UI
                    const likeCount = this.parentElement.querySelector('.like-count');
                    let currentCount = parseInt(likeCount.textContent);
                    
                    if (action === 'like') {
                        currentCount++;
                        this.dataset.action = 'unlike';
                        this.innerHTML = '<i class="fas fa-heart"></i> Unlike';
                    } else {
                        currentCount--;
                        this.dataset.action = 'like';
                        this.innerHTML = '<i class="far fa-heart"></i> Like';
                    }
                    
                    likeCount.textContent = currentCount;
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
}

// Set up polling for direct messages
function setupMessagePolling() {
    const messageContainer = document.querySelector('.messages-body');
    const conversationId = messageContainer?.dataset.conversationId;
    
    if (messageContainer && conversationId) {
        // Poll for new messages every 5 seconds
        setInterval(() => {
            fetch(`/messages/${conversationId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Update the messages container with any new messages
                const messages = data.messages;
                let messagesHTML = '';
                
                messages.forEach(message => {
                    const bubbleClass = message.is_sender ? 'message-sender' : 'message-receiver';
                    messagesHTML += `
                        <div class="message-bubble ${bubbleClass}">
                            <div class="message-content">${message.content}</div>
                            <div class="message-time">${message.timestamp}</div>
                        </div>
                    `;
                });
                
                messageContainer.innerHTML = messagesHTML;
                messageContainer.scrollTop = messageContainer.scrollHeight;
            })
            .catch(error => console.error('Error:', error));
        }, 5000);
        
        // Handle message form submission
        const messageForm = document.querySelector('.message-form form');
        if (messageForm) {
            messageForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const messageInput = this.querySelector('input[name="message"]');
                const message = messageInput.value.trim();
                
                if (message) {
                    fetch(`/messages/${conversationId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: `message=${encodeURIComponent(message)}`
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            // Clear the input field
                            messageInput.value = '';
                            
                            // Add the new message to the container
                            const newMessage = data.message;
                            const messageElement = document.createElement('div');
                            messageElement.className = 'message-bubble message-sender';
                            messageElement.innerHTML = `
                                <div class="message-content">${newMessage.content}</div>
                                <div class="message-time">${newMessage.timestamp}</div>
                            `;
                            
                            messageContainer.appendChild(messageElement);
                            messageContainer.scrollTop = messageContainer.scrollHeight;
                        }
                    })
                    .catch(error => console.error('Error:', error));
                }
            });
        }
    }
}

// Set up polling for global chat
function setupChatPolling() {
    const chatContainer = document.querySelector('.chat-messages');
    
    if (chatContainer) {
        // Poll for new chat messages every 5 seconds
        setInterval(() => {
            fetch('/chat', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Update the chat container with any new messages
                const messages = data.messages;
                let messagesHTML = '';
                
                messages.forEach(message => {
                    messagesHTML += `
                        <div class="chat-message">
                            <div class="chat-sender">
                                ${message.user.name} 
                                <span class="badge ${message.user.user_type === 'student' ? 'bg-primary' : 'bg-success'}">
                                    ${message.user.user_type === 'student' ? 'Student' : 'University'}
                                </span>
                                <small class="text-muted">${message.timestamp}</small>
                            </div>
                            <div class="chat-content">${message.content}</div>
                        </div>
                    `;
                });
                
                chatContainer.innerHTML = messagesHTML;
                chatContainer.scrollTop = chatContainer.scrollHeight;
            })
            .catch(error => console.error('Error:', error));
        }, 5000);
        
        // Handle chat form submission
        const chatForm = document.querySelector('.chat-form form');
        if (chatForm) {
            chatForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const chatInput = this.querySelector('input[name="message"]');
                const message = chatInput.value.trim();
                
                if (message) {
                    fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: `message=${encodeURIComponent(message)}`
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            // Clear the input field
                            chatInput.value = '';
                        }
                    })
                    .catch(error => console.error('Error:', error));
                }
            });
        }
    }
}

// Set active nav item based on current page
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Auto-resize textarea as user types more content
function autoResizeTextarea() {
    const textareas = document.querySelectorAll('textarea.auto-resize');
    
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
}

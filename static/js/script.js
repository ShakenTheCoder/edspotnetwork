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
    let lastMessageId = null;
    
    if (messageContainer && conversationId) {
        // Get initial last message ID
        const messages = messageContainer.querySelectorAll('.message-bubble');
        if (messages.length > 0) {
            lastMessageId = messages[messages.length - 1].dataset.messageId;
        }
        
        // Poll for new messages every 5 seconds
        setInterval(() => {
            fetch(`/messages/${conversationId}?since=${lastMessageId || 0}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Only append new messages
                const messages = data.messages;
                messages.forEach(message => {
                    if (!document.querySelector(`[data-message-id="${message.id}"]`)) {
                        const bubbleClass = message.is_sender ? 'message-sender' : 'message-receiver';
                        const messageElement = document.createElement('div');
                        messageElement.className = `message-bubble ${bubbleClass}`;
                        messageElement.dataset.messageId = message.id;
                        messageElement.innerHTML = `
                            <div class="message-content">${message.content}</div>
                            <div class="message-time">${message.timestamp}</div>
                        `;
                        messageContainer.appendChild(messageElement);
                        lastMessageId = message.id;
                    }
                });
                
                if (messages.length > 0) {
                    messageContainer.scrollTop = messageContainer.scrollHeight;
                }
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
        // Get the most recent message ID to use as baseline for polling
        let lastMessageId = Array.from(document.querySelectorAll('.chat-message'))
            .map(el => parseInt(el.dataset.messageId || '0'))
            .reduce((max, id) => Math.max(max, id), 0);
            
        // Poll for new chat messages every 5 seconds
        setInterval(() => {
            fetch(`/chat?since=${lastMessageId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.messages && data.messages.length > 0) {
                    // Add only new messages instead of replacing the entire content
                    data.messages.forEach(message => {
                        // Create a new message element
                        const messageElement = document.createElement('div');
                        messageElement.className = 'chat-message';
                        messageElement.dataset.messageId = message.id;
                        
                        messageElement.innerHTML = `
                            <div class="chat-sender">
                                <a href="/profile/${message.user.id}" class="text-decoration-none">
                                    ${message.user.name}
                                </a>
                                <span class="badge ${message.user.user_type === 'student' ? 'bg-primary' : 'bg-success'} ms-1">
                                    ${message.user.user_type.charAt(0).toUpperCase() + message.user.user_type.slice(1)}
                                </span>
                                <small class="text-muted">${message.timestamp}</small>
                            </div>
                            <div class="chat-content">${message.content}</div>
                        `;
                        
                        // Add to chat container
                        chatContainer.appendChild(messageElement);
                        
                        // Update last message ID
                        lastMessageId = Math.max(lastMessageId, message.id);
                    });
                    
                    // Scroll to bottom to show new messages
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            })
            .catch(error => console.error('Error fetching chat messages:', error));
        }, 5000);
        
        // Handle chat form submission with AJAX
        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');
        
        if (chatForm && messageInput) {
            chatForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const message = messageInput.value.trim();
                if (!message) return;
                
                fetch(chatForm.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: new URLSearchParams({
                        'message': message
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Clear the input field
                        messageInput.value = '';
                        
                        // Create and add the new message element
                        const messageElement = document.createElement('div');
                        messageElement.className = 'chat-message';
                        messageElement.dataset.messageId = data.message.id;
                        
                        messageElement.innerHTML = `
                            <div class="chat-sender">
                                <a href="/profile/${data.message.user.id}" class="text-decoration-none">
                                    ${data.message.user.name}
                                </a>
                                <span class="badge ${data.message.user.user_type === 'student' ? 'bg-primary' : 'bg-success'} ms-1">
                                    ${data.message.user.user_type.charAt(0).toUpperCase() + data.message.user.user_type.slice(1)}
                                </span>
                                <small class="text-muted">${data.message.timestamp}</small>
                            </div>
                            <div class="chat-content">${data.message.content}</div>
                        `;
                        
                        // Add to chat container and scroll to show it
                        chatContainer.appendChild(messageElement);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                        
                        // Update the last message ID
                        lastMessageId = data.message.id;
                    }
                })
                .catch(error => console.error('Error sending message:', error));
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

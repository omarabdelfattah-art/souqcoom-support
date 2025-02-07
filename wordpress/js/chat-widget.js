jQuery(document).ready(function($) {
    const widget = $('#souqcoom-support-widget');
    const messagesContainer = widget.find('.chat-messages');
    const input = widget.find('textarea');
    const sendBtn = widget.find('.send-btn');
    const minimizeBtn = widget.find('.minimize-btn');
    let isTyping = false;

    // Minimize/Maximize widget with animation
    minimizeBtn.on('click', function() {
        widget.toggleClass('minimized');
        if (widget.hasClass('minimized')) {
            minimizeBtn.html('&#x2B;'); // Plus sign
        } else {
            minimizeBtn.html('&#x2212;'); // Minus sign
        }
    });

    // Show typing indicator
    function showTypingIndicator() {
        const indicator = $('<div class="typing-indicator"><span></span><span></span><span></span></div>');
        messagesContainer.append(indicator);
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
    }

    // Remove typing indicator
    function removeTypingIndicator() {
        $('.typing-indicator').remove();
    }

    // Handle message sending with animations
    function sendMessage() {
        const message = input.val().trim();
        if (!message || isTyping) return;

        // Add user message with animation
        addMessage(message, 'user');
        input.val('');
        isTyping = true;

        // Show typing indicator
        showTypingIndicator();

        // Send message to API
        $.ajax({
            url: souqcoomSupport.apiUrl,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: message }),
            success: function(response) {
                removeTypingIndicator();
                addMessage(response.message, 'assistant');
                isTyping = false;
            },
            error: function(error) {
                removeTypingIndicator();
                addMessage('Sorry, I encountered an error. Please try again.', 'assistant error');
                isTyping = false;
            }
        });
    }

    // Add message to chat with animation
    function addMessage(content, type) {
        const messageDiv = $('<div>')
            .addClass('message')
            .addClass(`${type}-message`)
            .css('opacity', '0')
            .text(content);
        
        messagesContainer.append(messageDiv);
        
        // Trigger reflow for animation
        messageDiv[0].offsetHeight;
        
        messageDiv.css({
            'opacity': '1',
            'transform': 'translateY(0)'
        });
        
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
    }

    // Textarea auto-resize
    input.on('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Send message on button click or Enter key
    sendBtn.on('click', sendMessage);
    input.on('keypress', function(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Add welcome message with delay for animation
    setTimeout(() => {
        addMessage('👋 Welcome to Souqcoom Support! How can I assist you today?', 'assistant');
    }, 500);
});

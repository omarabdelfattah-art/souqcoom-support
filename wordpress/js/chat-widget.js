jQuery(document).ready(function($) {
    const widget = $('#souqcoom-support-widget');
    const messagesContainer = widget.find('.chat-messages');
    const input = widget.find('textarea');
    const sendBtn = widget.find('.send-btn');
    const minimizeBtn = widget.find('.minimize-btn');

    // Minimize/Maximize widget
    minimizeBtn.on('click', function() {
        widget.toggleClass('minimized');
        if (widget.hasClass('minimized')) {
            minimizeBtn.text('□');
        } else {
            minimizeBtn.text('_');
        }
    });

    // Handle message sending
    function sendMessage() {
        const message = input.val().trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        input.val('');

        // Send message to API
        $.ajax({
            url: souqcoomSupport.apiUrl,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: message }),
            success: function(response) {
                addMessage(response.message, 'assistant');
            },
            error: function(error) {
                addMessage('Sorry, I encountered an error. Please try again.', 'assistant error');
            }
        });
    }

    // Add message to chat
    function addMessage(content, type) {
        const messageDiv = $('<div>')
            .addClass('message')
            .addClass(`${type}-message`)
            .text(content);
        
        messagesContainer.append(messageDiv);
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
    }

    // Send message on button click or Enter key
    sendBtn.on('click', sendMessage);
    input.on('keypress', function(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Add welcome message
    addMessage('👋 Hello! How can I help you with Souqcoom today?', 'assistant');
});

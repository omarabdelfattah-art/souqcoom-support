jQuery(document).ready(function($) {
    // Toggle chat widget
    $('.souqcoom-chat-toggle').click(function() {
        $('.souqcoom-chatbot').addClass('active');
        $(this).hide();
        $('body').addClass('chat-open');
        // Focus input after animation
        setTimeout(() => {
            $('.chat-input textarea').focus();
        }, 300);
        history.pushState(null, document.title, window.location.href);
    });

    // Close chat widget
    $('.close-chat').click(function() {
        $('.souqcoom-chatbot').removeClass('active');
        $('.souqcoom-chat-toggle').show();
        $('body').removeClass('chat-open');
    });

    const chatbox = $(".chatbox");
    const textarea = $(".chat-input textarea");
    const sendBtn = $("#send-btn");
    let isProcessing = false;

    const createChatLi = (message, className) => {
        const chatLi = $("<li>").addClass("chat " + className);
        const formattedMessage = message.replace(/\n/g, '<br>');
        chatLi.html(`<p>${formattedMessage}</p>`);
        return chatLi;
    }

    const handleChat = async () => {
        if (isProcessing) return;

        const userMessage = textarea.val().trim();
        if(!userMessage) return;

        isProcessing = true;
        textarea.val("");
        textarea.css("height", "40px");
        sendBtn.prop('disabled', true);

        chatbox.append(createChatLi(userMessage, "outgoing"));
        chatbox.scrollTop(chatbox[0].scrollHeight);

        try {
            const response = await $.ajax({
                url: souqcoom_ajax.ajax_url,
                type: 'POST',
                data: {
                    action: 'souqcoom_chat_message',
                    message: userMessage,
                    nonce: souqcoom_ajax.nonce
                }
            });

            if(response.success) {
                chatbox.append(createChatLi(response.data, "incoming"));
            } else {
                chatbox.append(createChatLi("Sorry, something went wrong. Please try again.", "incoming"));
            }
        } catch(error) {
            console.error('Error:', error);
            chatbox.append(createChatLi("Sorry, something went wrong. Please try again.", "incoming"));
        } finally {
            chatbox.scrollTop(chatbox[0].scrollHeight);
            isProcessing = false;
            sendBtn.prop('disabled', false);
        }
    }

    // Handle textarea auto-resize
    textarea.on("input", function() {
        $(this).css("height", "40px");
        const height = Math.min(this.scrollHeight, 100);
        $(this).css("height", height + "px");
    });

    // Handle Enter key
    textarea.on("keydown", function(e) {
        // Send on Enter (but not on mobile or when Shift is pressed)
        if(e.key === "Enter" && !e.shiftKey && window.innerWidth > 768) {
            e.preventDefault();
            handleChat();
        }
    });

    // Handle send button click
    sendBtn.click(handleChat);

    // Prevent body scroll when scrolling chat
    chatbox.on('touchmove', function(e) {
        e.stopPropagation();
    });

    // Handle keyboard showing/hiding on mobile
    if ('visualViewport' in window) {
        window.visualViewport.addEventListener('resize', function() {
            if (window.innerWidth <= 768) {
                const viewport = window.visualViewport;
                $('.souqcoom-chatbot .chat-input').css('bottom', viewport.offsetTop + 'px');
            }
        });
    }

    // Handle back button on mobile
    $(window).on('popstate', function() {
        if ($('.souqcoom-chatbot').hasClass('active')) {
            $('.close-chat').click();
            history.pushState(null, document.title, window.location.href);
        }
    });
});

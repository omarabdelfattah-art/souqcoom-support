jQuery(document).ready(function($) {
    // Toggle chat widget
    $('.souqcoom-chat-toggle').click(function() {
        $('.souqcoom-chatbot').addClass('active');
        $(this).hide();
    });

    // Close chat widget
    $('.close-chat').click(function() {
        $('.souqcoom-chatbot').removeClass('active');
        $('.souqcoom-chat-toggle').show();
    });

    const chatbox = $(".chatbox");
    const textarea = $(".chat-input textarea");
    const sendBtn = $("#send-btn");

    const createChatLi = (message, className) => {
        const chatLi = $("<li>").addClass("chat " + className);
        const formattedMessage = message.replace(/\n/g, '<br>');
        chatLi.html(`<p>${formattedMessage}</p>`);
        return chatLi;
    }

    const handleChat = async () => {
        const userMessage = textarea.val().trim();
        if(!userMessage) return;

        textarea.val("");
        textarea.css("height", "48px");

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
                chatbox.scrollTop(chatbox[0].scrollHeight);
            } else {
                chatbox.append(createChatLi("Sorry, something went wrong. Please try again.", "incoming"));
                chatbox.scrollTop(chatbox[0].scrollHeight);
            }
        } catch(error) {
            console.error('Error:', error);
            chatbox.append(createChatLi("Sorry, something went wrong. Please try again.", "incoming"));
            chatbox.scrollTop(chatbox[0].scrollHeight);
        }
    }

    // Handle textarea auto-resize
    textarea.on("input", function() {
        $(this).css("height", "48px");
        const height = Math.min(this.scrollHeight, 120);
        $(this).css("height", height + "px");
    });

    // Handle Enter key
    textarea.on("keydown", function(e) {
        if(e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
            e.preventDefault();
            handleChat();
        }
    });

    // Handle send button click
    sendBtn.click(handleChat);
});

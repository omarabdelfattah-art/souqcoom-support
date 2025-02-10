(function($) {
    'use strict';

    class SouqcoomChat {
        constructor() {
            // Cache DOM elements
            this.widget = $('.souqcoom-chat-widget');
            this.chatbot = $('.souqcoom-chatbot');
            this.chatbox = $('.chatbox');
            this.textarea = $('.chat-input textarea');
            this.sendBtn = $('#send-btn');
            this.toggleBtn = $('.souqcoom-chat-toggle');
            this.closeBtn = $('.close-chat');
            this.isProcessing = false;

            // Initialize
            this.initializeEventListeners();
            this.checkUrlForChatOpen();
        }

        initializeEventListeners() {
            // Toggle chat widget
            this.toggleBtn.on('click', () => this.openChat());
            this.closeBtn.on('click', () => this.closeChat());

            // Handle send message
            this.sendBtn.on('click', () => this.handleChat());
            this.textarea.on('keydown', (e) => this.handleKeyPress(e));
            this.textarea.on('input', () => this.handleTextareaResize());

            // Handle mobile-specific events
            this.handleMobileEvents();

            // Handle back button
            $(window).on('popstate', () => this.handlePopState());

            // Set initial placeholder
            this.textarea.attr('placeholder', souqcoom_ajax.strings.placeholder);
        }

        openChat() {
            this.chatbot.addClass('active').attr('aria-hidden', 'false');
            this.toggleBtn.hide().attr('aria-expanded', 'true');
            $('body').addClass('chat-open');
            
            // Focus input after animation
            setTimeout(() => this.textarea.focus(), 300);
            
            // Add history state
            history.pushState({ chat: 'open' }, document.title, window.location.href);
        }

        closeChat() {
            this.chatbot.removeClass('active').attr('aria-hidden', 'true');
            this.toggleBtn.show().attr('aria-expanded', 'false');
            $('body').removeClass('chat-open');
            history.pushState(null, document.title, window.location.href);
        }

        createChatMessage(message, className) {
            const chatLi = $('<li>').addClass('chat ' + className);
            const formattedMessage = message.replace(/\n/g, '<br>');
            chatLi.html(`<p>${formattedMessage}</p>`);
            return chatLi;
        }

        createLoadingMessage() {
            return $('<div>').addClass('chat-loading')
                .append($('<span>'))
                .append($('<span>'))
                .append($('<span>'));
        }

        async handleChat() {
            if (this.isProcessing) return;

            const userMessage = this.textarea.val().trim();
            if (!userMessage) return;

            this.isProcessing = true;
            this.textarea.val('').prop('disabled', true);
            this.textarea.css('height', '40px');
            this.sendBtn.prop('disabled', true);

            // Add user message
            this.chatbox.append(this.createChatMessage(userMessage, 'outgoing'));
            this.scrollToBottom();

            // Add loading animation
            const loadingMessage = this.createLoadingMessage();
            this.chatbox.append(loadingMessage);
            this.scrollToBottom();

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

                // Remove loading animation
                loadingMessage.remove();

                if (response.success) {
                    this.chatbox.append(this.createChatMessage(response.data, 'incoming'));
                } else {
                    throw new Error(response.data);
                }
            } catch (error) {
                console.error('Chat Error:', error);
                loadingMessage.remove();
                this.chatbox.append(
                    this.createChatMessage(souqcoom_ajax.strings.error_message, 'incoming')
                );
            } finally {
                this.isProcessing = false;
                this.textarea.prop('disabled', false).focus();
                this.sendBtn.prop('disabled', false);
                this.scrollToBottom();
            }
        }

        handleKeyPress(e) {
            // Send on Enter (but not on mobile or when Shift is pressed)
            if (e.key === 'Enter' && !e.shiftKey && window.innerWidth > 768) {
                e.preventDefault();
                this.handleChat();
            }
        }

        handleTextareaResize() {
            this.textarea.css('height', '40px');
            const height = Math.min(this.textarea[0].scrollHeight, 100);
            this.textarea.css('height', height + 'px');
        }

        handleMobileEvents() {
            // Prevent body scroll when scrolling chat
            this.chatbox.on('touchmove', (e) => e.stopPropagation());

            // Handle keyboard showing/hiding on mobile
            if ('visualViewport' in window) {
                window.visualViewport.addEventListener('resize', () => {
                    if (window.innerWidth <= 768) {
                        const viewport = window.visualViewport;
                        $('.souqcoom-chatbot .chat-input').css('bottom', viewport.offsetTop + 'px');
                    }
                });
            }
        }

        handlePopState(e) {
            const state = e && e.state;
            if (state && state.chat === 'open') {
                this.openChat();
            } else {
                this.closeChat();
            }
        }

        checkUrlForChatOpen() {
            // Check if URL has #chat hash
            if (window.location.hash === '#chat') {
                this.openChat();
                // Remove the hash without triggering a jump
                history.replaceState(null, document.title, window.location.pathname + window.location.search);
            }
        }

        scrollToBottom() {
            this.chatbox.stop().animate({
                scrollTop: this.chatbox[0].scrollHeight
            }, 300);
        }
    }

    // Initialize chat when document is ready
    $(document).ready(() => {
        window.souqcoomChat = new SouqcoomChat();
    });

})(jQuery);

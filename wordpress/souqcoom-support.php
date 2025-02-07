<?php
/*
Plugin Name: Souqcoom Support Chat
Description: AI-powered support chat for Souqcoom
Version: 1.0
Author: Your Name
*/

// Prevent direct access to this file
if (!defined('ABSPATH')) {
    exit;
}

// Add chat widget script and styles
function souqcoom_support_enqueue_scripts() {
    wp_enqueue_style('souqcoom-support-style', plugins_url('css/chat-widget.css', __FILE__));
    wp_enqueue_script('souqcoom-support-script', plugins_url('js/chat-widget.js', __FILE__), array('jquery'), '1.0', true);
    wp_localize_script('souqcoom-support-script', 'souqcoomSupport', array(
        'apiUrl' => 'https://souqcoom-support.vercel.app/chat'  // Vercel deployment URL
    ));
}
add_action('wp_enqueue_scripts', 'souqcoom_support_enqueue_scripts');

// Add chat widget HTML
function souqcoom_support_add_chat_widget() {
    ?>
    <div id="souqcoom-support-widget" class="souqcoom-widget-container">
        <div class="chat-header">
            <div class="header-left">
                <img src="<?php echo plugins_url('images/souqcoom-icon.png', __FILE__); ?>" alt="Souqcoom Support" class="support-icon" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMThjLTQuNDEgMC04LTMuNTktOC04czMuNTktOCA4LTggOCAzLjU5IDggOC0zLjU5IDgtOCA4eiIvPjxwYXRoIGQ9Ik0xMiA2Yy0zLjMxIDAtNiAyLjY5LTYgNnMyLjY5IDYgNiA2IDYtMi42OSA2LTYtMi42OS02LTYtNnptMCAxMGMtMi4yMSAwLTQtMS43OS00LTRzMS43OS00IDQtNCA0IDEuNzkgNCA0LTEuNzkgNC00IDR6Ii8+PC9zdmc+'" />
                <h3>Souqcoom Support</h3>
            </div>
            <button class="minimize-btn" aria-label="Minimize chat">−</button>
        </div>
        <div class="chat-messages"></div>
        <div class="chat-input">
            <textarea 
                placeholder="Type your message here..." 
                aria-label="Chat message"
                rows="1"
            ></textarea>
            <button class="send-btn" aria-label="Send message">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            </button>
        </div>
    </div>
    <?php
}
add_action('wp_footer', 'souqcoom_support_add_chat_widget');

// Add settings page
function souqcoom_support_add_admin_menu() {
    add_options_page(
        'Souqcoom Support Settings',
        'Souqcoom Support',
        'manage_options',
        'souqcoom-support',
        'souqcoom_support_settings_page'
    );
}
add_action('admin_menu', 'souqcoom_support_add_admin_menu');

function souqcoom_support_settings_page() {
    ?>
    <div class="wrap">
        <h1>Souqcoom Support Settings</h1>
        <form method="post" action="options.php">
            <?php
            settings_fields('souqcoom_support_options');
            do_settings_sections('souqcoom-support');
            submit_button();
            ?>
        </form>
    </div>
    <?php
}

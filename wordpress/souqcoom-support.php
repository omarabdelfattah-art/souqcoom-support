<?php
/*
Plugin Name: Souqcoom Support Chat
Plugin URI: https://souq.com
Description: A modern chat support widget for Souq.com
Version: 1.0
Author: Your Name
Author URI: https://souq.com
*/

// Prevent direct access to this file
if (!defined('ABSPATH')) {
    exit;
}

// Enqueue necessary scripts and styles
function souqcoom_enqueue_scripts() {
    // Enqueue Font Awesome
    wp_enqueue_style('font-awesome', 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
    
    // Enqueue custom styles
    wp_enqueue_style('souqcoom-chat-style', plugins_url('css/style.css', __FILE__));
    
    // Enqueue jQuery
    wp_enqueue_script('jquery');
    
    // Enqueue custom script
    wp_enqueue_script('souqcoom-chat-script', plugins_url('js/chat.js', __FILE__), array('jquery'), '1.0', true);
    
    // Localize the script with new data
    wp_localize_script('souqcoom-chat-script', 'souqcoom_ajax', array(
        'ajax_url' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('souqcoom_chat_nonce')
    ));
}
add_action('wp_enqueue_scripts', 'souqcoom_enqueue_scripts');

// Add chat widget HTML
function souqcoom_add_chat_widget() {
    ?>
    <div class="souqcoom-chat-widget">
        <div class="souqcoom-chat-toggle">
            <i class="fas fa-comments"></i>
        </div>
        <div class="souqcoom-chatbot">
            <header>
                <div class="header-content">
                    <i class="fas fa-shopping-bag"></i>
                    <h2>Souq.com Support</h2>
                </div>
                <div class="close-chat">
                    <i class="fas fa-times"></i>
                </div>
            </header>
            <ul class="chatbox">
                <li class="chat incoming">
                    <p>👋 مرحباً بك في دعم سوق.كوم! كيف يمكنني مساعدتك اليوم؟<br>Hello! Welcome to Souq.com support! How can I assist you today?</p>
                </li>
            </ul>
            <div class="chat-input">
                <textarea placeholder="Type your message here..." required></textarea>
                <button id="send-btn">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>
    <?php
}
add_action('wp_footer', 'souqcoom_add_chat_widget');

// Handle AJAX chat messages
function souqcoom_handle_chat_message() {
    // Verify nonce
    if (!isset($_POST['nonce']) || !wp_verify_nonce($_POST['nonce'], 'souqcoom_chat_nonce')) {
        wp_send_json_error('Invalid nonce');
    }

    // Get the message
    $message = sanitize_textarea_field($_POST['message']);
    
    // Call the AI chat API
    $api_url = 'https://souqcoom-support.vercel.app/chat';
    $response = wp_remote_post($api_url, array(
        'headers'     => array('Content-Type' => 'application/json'),
        'body'        => json_encode(array('message' => $message)),
        'timeout'     => 45
    ));
    
    if (is_wp_error($response)) {
        wp_send_json_error('Sorry, there was an error connecting to the chat service.');
        return;
    }
    
    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);
    
    if (isset($data['message']) && $data['status'] === 'success') {
        wp_send_json_success($data['message']);
    } else {
        wp_send_json_error($data['detail'] ?? 'Sorry, there was an error processing your message.');
    }
}
add_action('wp_ajax_souqcoom_chat_message', 'souqcoom_handle_chat_message');
add_action('wp_ajax_nopriv_souqcoom_chat_message', 'souqcoom_handle_chat_message');

// Add settings page
function souqcoom_add_admin_menu() {
    add_options_page(
        'Souqcoom Support Settings',
        'Souqcoom Support',
        'manage_options',
        'souqcoom-support',
        'souqcoom_settings_page'
    );
}
add_action('admin_menu', 'souqcoom_add_admin_menu');

// Create the settings page
function souqcoom_settings_page() {
    ?>
    <div class="wrap">
        <h1>Souqcoom Support Settings</h1>
        <form method="post" action="options.php">
            <?php
            settings_fields('souqcoom_options');
            do_settings_sections('souqcoom-support');
            submit_button();
            ?>
        </form>
    </div>
    <?php
}

// Register settings
function souqcoom_register_settings() {
    register_setting('souqcoom_options', 'souqcoom_api_key');
    
    add_settings_section(
        'souqcoom_settings_section',
        'API Settings',
        'souqcoom_settings_section_callback',
        'souqcoom-support'
    );
    
    add_settings_field(
        'souqcoom_api_key',
        'API Key',
        'souqcoom_api_key_render',
        'souqcoom-support',
        'souqcoom_settings_section'
    );
}
add_action('admin_init', 'souqcoom_register_settings');

function souqcoom_settings_section_callback() {
    echo 'Enter your API settings below:';
}

function souqcoom_api_key_render() {
    $api_key = get_option('souqcoom_api_key');
    ?>
    <input type='text' name='souqcoom_api_key' value='<?php echo esc_attr($api_key); ?>'>
    <?php
}

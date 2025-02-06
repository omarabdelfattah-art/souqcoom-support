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
        'apiUrl' => 'https://souqcoom-support.yourusername.repl.co/chat'  // Replace with your actual Replit URL
    ));
}
add_action('wp_enqueue_scripts', 'souqcoom_support_enqueue_scripts');

// Add chat widget HTML
function souqcoom_support_add_chat_widget() {
    ?>
    <div id="souqcoom-support-widget" class="souqcoom-widget-container">
        <div class="chat-header">
            <span class="support-icon">💬</span>
            <h3>Souqcoom Support</h3>
            <button class="minimize-btn">_</button>
        </div>
        <div class="chat-messages"></div>
        <div class="chat-input">
            <textarea placeholder="Ask me anything about Souqcoom..."></textarea>
            <button class="send-btn">Send</button>
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

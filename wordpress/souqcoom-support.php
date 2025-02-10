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

// Define plugin constants
define('SOUQCOOM_VERSION', '1.0.0');
define('SOUQCOOM_PLUGIN_FILE', __FILE__);
define('SOUQCOOM_PLUGIN_PATH', plugin_dir_path(__FILE__));
define('SOUQCOOM_PLUGIN_URL', plugin_dir_url(__FILE__));

// Plugin initialization
function souqcoom_init() {
    // Load plugin text domain for translations
    load_plugin_textdomain('souqcoom-support', false, dirname(plugin_basename(__FILE__)) . '/languages');
}
add_action('init', 'souqcoom_init');

// Plugin activation
function souqcoom_activate() {
    // Create any necessary database tables or options
    add_option('souqcoom_version', SOUQCOOM_VERSION);
    
    // Clear the permalinks
    flush_rewrite_rules();
}
register_activation_hook(__FILE__, 'souqcoom_activate');

// Plugin deactivation
function souqcoom_deactivate() {
    // Clean up if necessary
    flush_rewrite_rules();
}
register_deactivation_hook(__FILE__, 'souqcoom_deactivate');

// Enqueue necessary scripts and styles
function souqcoom_enqueue_scripts() {
    // Get file modification times for versioning
    $css_ver = filemtime(plugin_dir_path(__FILE__) . 'css/style.css');
    $js_ver = filemtime(plugin_dir_path(__FILE__) . 'js/chat.js');

    // Enqueue Font Awesome
    wp_enqueue_style(
        'font-awesome',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
        array(),
        '6.0.0'
    );

    // Enqueue our styles
    wp_enqueue_style(
        'souqcoom-chat-style',
        plugins_url('css/style.css', __FILE__),
        array('font-awesome'),
        $css_ver
    );

    // Enqueue jQuery
    wp_enqueue_script('jquery');

    // Enqueue our script
    wp_enqueue_script(
        'souqcoom-chat-script',
        plugins_url('js/chat.js', __FILE__),
        array('jquery'),
        $js_ver,
        true
    );

    // Localize script with necessary data
    wp_localize_script('souqcoom-chat-script', 'souqcoom_ajax', array(
        'ajax_url' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('souqcoom_chat_nonce'),
        'is_rtl' => is_rtl(),
        'lang' => get_locale(),
        'strings' => array(
            'error_message' => __('Sorry, something went wrong. Please try again.', 'souqcoom-support'),
            'placeholder' => __('Type your message here...', 'souqcoom-support'),
            'sending' => __('Sending...', 'souqcoom-support')
        )
    ));
}
add_action('wp_enqueue_scripts', 'souqcoom_enqueue_scripts');

// Add chat widget HTML
function souqcoom_add_chat_widget() {
    // Don't display in admin area
    if (is_admin()) {
        return;
    }
    
    // Get language direction
    $dir = is_rtl() ? 'rtl' : 'ltr';
    echo souqcoom_chat_widget_html();
}
add_action('wp_footer', 'souqcoom_add_chat_widget');

function souqcoom_chat_widget_html() {
    ob_start();
    ?>
    <div class="souqcoom-chat-widget">
        <button class="souqcoom-chat-toggle" aria-label="Toggle chat" aria-expanded="false">
            <i class="fas fa-comments"></i>
        </button>
        
        <div class="souqcoom-chatbot" role="dialog" aria-label="Chat Support" aria-hidden="true">
            <header>
                <div class="header-content">
                    <i class="fas fa-robot"></i>
                    <h2>Souq.com Support</h2>
                </div>
                <button class="close-chat" aria-label="Close chat">
                    <i class="fas fa-times"></i>
                </button>
            </header>
            
            <ul class="chatbox" role="log" aria-live="polite">
                <li class="chat incoming">
                    <p>Hello! 👋 I'm your Souq.com support assistant. How can I help you today?</p>
                </li>
            </ul>
            
            <div class="chat-input">
                <textarea 
                    placeholder="Type your message here..." 
                    aria-label="Type your message"
                    rows="1"
                ></textarea>
                <button id="send-btn" aria-label="Send message">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>
    <?php
    return ob_get_clean();
}

// Handle AJAX chat messages
function souqcoom_handle_chat_message() {
    // Verify nonce
    if (!isset($_POST['nonce']) || !wp_verify_nonce($_POST['nonce'], 'souqcoom_chat_nonce')) {
        wp_send_json_error('Invalid security token');
        exit;
    }

    // Get and sanitize message
    $message = isset($_POST['message']) ? sanitize_textarea_field($_POST['message']) : '';
    if (empty($message)) {
        wp_send_json_error('Message is required');
        exit;
    }

    try {
        // Prepare API request
        $api_url = 'https://souqcoom-support.vercel.app/chat';
        $response = wp_remote_post($api_url, array(
            'timeout' => 15,
            'headers' => array(
                'Content-Type' => 'application/json',
            ),
            'body' => json_encode(array(
                'message' => $message,
                'language' => is_rtl() ? 'ar' : 'en'
            ))
        ));

        // Check for errors
        if (is_wp_error($response)) {
            throw new Exception($response->get_error_message());
        }

        // Parse response
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);

        if (!$data || isset($data['error'])) {
            throw new Exception(isset($data['error']) ? $data['error'] : 'Invalid response from API');
        }

        // Send success response
        wp_send_json_success($data['response']);

    } catch (Exception $e) {
        // Log error for debugging
        error_log('Souqcoom Chat Error: ' . $e->getMessage());
        wp_send_json_error('Sorry, there was a problem processing your request. Please try again.');
    }

    exit;
}
add_action('wp_ajax_souqcoom_chat_message', 'souqcoom_handle_chat_message');
add_action('wp_ajax_nopriv_souqcoom_chat_message', 'souqcoom_handle_chat_message');

// Add settings page
function souqcoom_add_settings_page() {
    add_options_page(
        __('Souqcoom Support Settings', 'souqcoom-support'),
        __('Souqcoom Support', 'souqcoom-support'),
        'manage_options',
        'souqcoom-support',
        'souqcoom_settings_page'
    );
}
add_action('admin_menu', 'souqcoom_add_settings_page');

// Settings page content
function souqcoom_settings_page() {
    if (!current_user_can('manage_options')) {
        return;
    }
    ?>
    <div class="wrap">
        <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
        <form action="options.php" method="post">
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
    register_setting('souqcoom_options', 'souqcoom_settings', array(
        'type' => 'array',
        'sanitize_callback' => 'souqcoom_sanitize_settings'
    ));

    add_settings_section(
        'souqcoom_settings_section',
        __('Chat Widget Settings', 'souqcoom-support'),
        'souqcoom_settings_section_callback',
        'souqcoom-support'
    );

    add_settings_field(
        'souqcoom_api_url',
        __('API URL', 'souqcoom-support'),
        'souqcoom_api_url_callback',
        'souqcoom-support',
        'souqcoom_settings_section'
    );
}
add_action('admin_init', 'souqcoom_register_settings');

// Settings callbacks
function souqcoom_settings_section_callback() {
    echo '<p>' . esc_html__('Configure your Souqcoom Support chat widget settings below.', 'souqcoom-support') . '</p>';
}

function souqcoom_api_url_callback() {
    $options = get_option('souqcoom_settings', array());
    $api_url = isset($options['api_url']) ? $options['api_url'] : 'https://souqcoom-support.vercel.app/chat';
    ?>
    <input type="url" name="souqcoom_settings[api_url]" value="<?php echo esc_attr($api_url); ?>" class="regular-text">
    <p class="description">
        <?php esc_html_e('Enter the API URL for the chat service.', 'souqcoom-support'); ?>
    </p>
    <?php
}

// Sanitize settings
function souqcoom_sanitize_settings($input) {
    $sanitized = array();
    if (isset($input['api_url'])) {
        $sanitized['api_url'] = esc_url_raw($input['api_url']);
    }
    return $sanitized;
}

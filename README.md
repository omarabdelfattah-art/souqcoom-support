# Souqcoom Support

An AI-powered support assistant specifically trained on Souqcoom's partnership and marketing program documentation, built with Mistral AI and Streamlit.

## Setup

1. Clone this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Get your Mistral AI API key from [Mistral AI Platform](https://console.mistral.ai/)
4. Add your API key to the `.env` file:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

## Running the Application

To run the support assistant:

```bash
streamlit run app.py
```

The application will open in your default web browser.

## Features

- Trained on Souqcoom's official documentation
- Answers questions about partnership programs, policies, and procedures
- Provides accurate information about terms, conditions, and requirements
- Supports both English and Arabic queries
- Clean and intuitive chat interface
- Real-time responses from Mistral AI
- Message history preservation during session
- Configurable model parameters
- Responsive web design

## Training Data

The support assistant has been trained on Souqcoom's official documentation, including:
- Partnership and Marketing Program guidelines
- Terms and conditions
- Payment and commission policies
- Data protection and privacy policies
- Shipping and return policies

## Usage

1. Start the application
2. Ask questions about Souqcoom's partnership program
3. Get instant, accurate responses based on official documentation
4. Available in both English and Arabic

## Deployment

### Free Deployment Options

#### 1. Render.com (Recommended)

1. Create a free account on [Render.com](https://render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository or use the public git URL
4. Configure your service:
   - Name: souqcoom-support-api
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - MISTRAL_API_KEY: Your Mistral AI API key

The free tier includes:
- 750 hours of runtime per month
- 512 MB RAM
- Shared CPU
- Automatic HTTPS/SSL
- Custom domains supported

#### 2. Alternative: Railway.app

1. Create account on [Railway.app](https://railway.app)
2. Create new project
3. Deploy from GitHub
4. Add environment variables
5. Deploy

#### 3. Alternative: Fly.io

1. Create account on [Fly.io](https://fly.io)
2. Install flyctl
3. Run `fly launch`
4. Deploy with `fly deploy`

## Update WordPress Plugin

After deploying, update the API URL in `wordpress/souqcoom-support.php`:

```php
wp_localize_script('souqcoom-support-script', 'souqcoomSupport', array(
    'apiUrl' => 'https://your-app.onrender.com/chat'
));
```

## Local Development

1. Create virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: .\env\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the API:
```bash
uvicorn api:app --reload
```

## Environment Variables

Create a `.env` file with:
```
MISTRAL_API_KEY=your_api_key_here
```

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat endpoint
  - Request body: `{"message": "Your message here"}`
  - Response: `{"message": "AI response", "status": "success"}`

## Note

Make sure to keep your API key confidential and never share it publicly.

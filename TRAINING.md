# Training Your Mistral AI Chatbot

This guide explains how to train and fine-tune your chatbot using custom data.

## Training Data Format

Training data is stored in JSONL format (JSON Lines) where each line contains a conversation example with a user message and the desired assistant response. The data is stored in `training_data/training_examples.jsonl`.

Example format:
```json
{"messages": [{"role": "user", "content": "What services do you offer?"}, {"role": "assistant", "content": "I can help you with..."}]}
```

## How to Train the Chatbot

1. **Prepare Training Data**:
   - Add training examples to `training_data/training_examples.jsonl`
   - Each example should include a user message and the desired assistant response
   - You can add examples manually or use the training script

2. **Using the Training Script**:
   ```bash
   python train_bot.py
   ```
   The script provides three options:
   - Add new training examples
   - Start fine-tuning process
   - Exit

3. **Adding Training Examples**:
   - Choose option 1 from the menu
   - Enter the user message
   - Enter the desired assistant response
   - The example will be added to the training file

4. **Start Fine-tuning**:
   - Choose option 2 from the menu
   - The script will:
     1. Upload your training file to Mistral AI
     2. Create a fine-tuning job
     3. Monitor the fine-tuning progress
     4. Provide the fine-tuned model ID when complete

5. **Using the Fine-tuned Model**:
   - Once fine-tuning is complete, update the model name in `web_app.py` or `cli_chat.py`
   - Replace "mistral-small-latest" with your fine-tuned model ID

## Best Practices

1. **Quality Training Data**:
   - Provide clear and consistent examples
   - Include a variety of scenarios
   - Make sure responses align with your desired tone and style

2. **Training Data Size**:
   - Start with at least 50-100 examples
   - More examples generally lead to better results
   - Ensure examples are diverse and cover different use cases

3. **Testing**:
   - Test the fine-tuned model thoroughly
   - Verify responses match your expectations
   - Add more training examples if needed

## Monitoring and Maintenance

1. **Regular Updates**:
   - Add new training examples as needed
   - Fine-tune periodically with new data
   - Monitor chatbot performance

2. **Error Handling**:
   - Check training logs for errors
   - Verify training examples format
   - Monitor fine-tuning job status

## Support

If you encounter any issues:
1. Check the Mistral AI documentation
2. Verify your API key and permissions
3. Ensure training data follows the correct format

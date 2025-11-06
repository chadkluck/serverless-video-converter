import json
import random
import logging
import os

# Do all imports and global configurations at top of the file
# This reduces the processing time for the Lambda function

# Configure logging based on environment
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
numeric_level = getattr(logging, log_level.upper(), logging.INFO)
logger.setLevel(numeric_level)

print("COLD START")

answers = [
    "It is certain",
    "It is decidedly so",
    "Without a doubt",
    "Yes definitely",
    "You may rely on it",
    "As I see it, yes",
    "Most likely",
    "Outlook good",
    "Yes",
    "Signs point to yes",
    "Reply hazy try again",
    "Ask again later",
    "Better not tell you now",
    "Cannot predict now",
    "Concentrate and ask again",
    "Don't count on it",
    "My reply is no",
    "My sources say no",
    "Outlook not so good"
]

def handler(event, context):
    """
    This is the handler function for your application referred to in the SAM
    template. It should be kept simple and used as the handler for the
    request. Business logic should be put in process_request()
    
    Args:
        event (dict): The event passed to the lambda function
        context (object): The context passed to the lambda function
    
    Returns:
        dict: Response with statusCode, body, and headers
    """
    try:
        response = process_request(event, context)
    except Exception as error:
        # Send error message and trace to CloudWatch logs
        logger.error(f"Error in 7G: {str(error)}", exc_info=True)
        response = {
            "statusCode": 500,
            "body": json.dumps({"status": 500, "message": "Internal server error in 7G"}),
            "headers": {"content-type": "application/json"}
        }
    
    return response


def process_request(event, context):
    """
    Process the request
    
    Args:
        event (dict): The event passed to the lambda function
        context (object): The context passed to the lambda function
    
    Returns:
        dict: Response to send up to AWS API Gateway
    """
    prediction = random.choice(answers)
    
    # Gets sent to CloudWatch logs
    logger.info(f"Prediction log: {prediction}")
    
    return {
        "statusCode": 200,
        "body": json.dumps({"prediction": prediction}),
        "headers": {"content-type": "application/json"}
    }

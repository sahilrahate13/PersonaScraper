# PersonaScraper
Reddit User Persona Generator
A Python script that analyzes Reddit user profiles and generates detailed user personas based on their posts and comments, using AI analysis with Google's Gemini API.
Features

Scrapes Reddit user posts and comments
Generates comprehensive user personas with 15+ characteristics
Uses Google Gemini AI for intelligent content analysis
Provides citations for each persona characteristic
Outputs detailed text reports
Follows PEP-8 guidelines

Setup Instructions
Prerequisites

Python 3.7 or higher
Reddit API credentials
Google Gemini API key

1. Clone the Repository
bashgit clone <your-repo-url>
cd reddit-persona-generator
2. Install Dependencies
bashpip install -r requirements.txt
3. Get API Credentials
Reddit API Setup:

Go to https://www.reddit.com/prefs/apps
Click "Create App" or "Create Another App"
Choose "script" as the app type
Note down your Client ID and Client Secret

Gemini API Setup:

Go to https://makersuite.google.com/app/apikey
Create a new API key
Copy the API key

4. Configure Credentials
You have two options:
Option A: Interactive Setup (Recommended)
Run the script and it will prompt you for credentials:
bashpython reddit_persona_generator.py
Option B: Environment Variables
Create a .env file in the project directory:
envREDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=PersonaGenerator/1.0
GEMINI_API_KEY=your_gemini_api_key_here
Usage
Basic Usage
bashpython reddit_persona_generator.py
Then follow the interactive prompts to:

Set up credentials (if not already configured)
Enter the Reddit profile URL
Wait for analysis to complete

Example
python# In Python script or Jupyter notebook
from reddit_persona_generator import generate_persona

# Generate persona for a user
persona = generate_persona("https://www.reddit.com/user/kojied/")
Command Line Usage
bash# Analyze a specific user
python -c "
from reddit_persona_generator import quick_setup, generate_persona
quick_setup('client_id', 'client_secret', 'gemini_key')
generate_persona('https://www.reddit.com/user/kojied/')
"
Output
The script generates:

A detailed text report saved as persona_username_YYYY-MM-DD.txt
Console output showing analysis progress
Summary of key persona characteristics

Sample Output Structure
================================================================================
                        REDDIT USER PERSONA REPORT
================================================================================

USERNAME: u/kojied
ANALYSIS DATE: 2024-01-15
ACCOUNT AGE: 1250 days
TOTAL POSTS: 45
TOTAL COMMENTS: 234
KARMA: 5670

================================================================================
                            PERSONA OVERVIEW
================================================================================

REPRESENTATIVE QUOTE: "I think the key is to stay curious and keep learning..."
Citations:
  1. [COMMENT] I think the key is to stay curious and keep learning...
     Source: https://reddit.com/r/programming/comments/xyz123/
     Subreddit: r/programming | Score: 156

...
Sample Outputs
This repository includes sample persona files for:

persona_kojied_2024-01-15.txt
persona_Hungry-Move-6603_2024-01-15.txt

Technical Details
Technologies Used

praw: Reddit API wrapper
google-generativeai: Gemini AI integration
python-dotenv: Environment variable management
requests: HTTP requests
beautifulsoup4: HTML parsing

Architecture

RedditUserPersonaGenerator: Main class handling the entire pipeline
UserPersona: Data structure for persona information
Citation: Data structure for source citations
AI-powered analysis using Google Gemini Pro

Rate Limiting
The script includes built-in rate limiting to respect Reddit's API limits (60 requests per minute).
Troubleshooting
Common Issues

"Reddit credentials not provided"

Ensure you've set up Reddit API credentials correctly
Check that your Reddit app is configured as "script" type


"Gemini API key not provided"

Verify your Gemini API key is correct
Ensure you have API access enabled


"User not found"

Check the Reddit username/URL is correct
Ensure the user profile is public


Rate limiting errors

The script includes automatic rate limiting
If issues persist, increase the delay between requests



Debug Mode
For debugging, you can modify the script to include verbose logging:
pythonimport logging
logging.basicConfig(level=logging.DEBUG)
Contributing

Fork the repository
Create a feature branch
Make your changes
Follow PEP-8 guidelines
Submit a pull request

License
This project is created for educational purposes as part of the BeyondChats internship assignment.
Contact
For questions or issues, please contact through the assignment platform.

Note: This script is designed to analyze public Reddit profiles only. Please respect user privacy and Reddit's terms of service.

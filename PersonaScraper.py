#!/usr/bin/env python
# coding: utf-8

# In[59]:


import subprocess
import sys

packages = [
    'praw',
    'google-generativeai',
    'python-dotenv',
    'requests',
    'beautifulsoup4'
]

for package in packages:
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"✓ Installed {package}")
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")


# In[63]:


import praw
import google.generativeai as genai
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import time


def install_packages():
    import subprocess
    import sys
    
    packages = [
        'praw',
        'google-generativeai',
        'python-dotenv',
        'requests',
        'beautifulsoup4'
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")



@dataclass
class Citation:
    """Represents a citation for a persona characteristic"""
    content: str
    post_type: str  # 'post' or 'comment'
    url: str
    created_utc: float
    subreddit: str
    score: int

@dataclass
class PersonaCharacteristic:
    """Represents a characteristic with its citations"""
    value: str
    citations: List[Citation]

@dataclass
class UserPersona:
    """Complete user persona structure"""
    # Basic Demographics
    estimated_age: PersonaCharacteristic
    occupation: PersonaCharacteristic
    location: PersonaCharacteristic
    relationship_status: PersonaCharacteristic
    
    # Personality Traits
    personality_type: PersonaCharacteristic
    interests: PersonaCharacteristic
    values: PersonaCharacteristic
    
    # Behavioral Patterns
    communication_style: PersonaCharacteristic
    online_behavior: PersonaCharacteristic
    activity_patterns: PersonaCharacteristic
    
    # Motivations & Goals
    primary_motivations: PersonaCharacteristic
    frustrations: PersonaCharacteristic
    goals: PersonaCharacteristic
    
    # Technical Profile
    tech_savviness: PersonaCharacteristic
    preferred_platforms: PersonaCharacteristic
    
    # Quote
    representative_quote: PersonaCharacteristic
    
    # Metadata
    username: str
    analysis_date: str
    total_posts: int
    total_comments: int
    account_age_days: int
    karma: int

class RedditUserPersonaGenerator:
    """Main class for generating user personas from Reddit profiles"""
    
    def __init__(self, reddit_client_id: str = None, reddit_client_secret: str = None, 
                 reddit_user_agent: str = None, gemini_api_key: str = None):
        """
        Initialize the persona generator
        
        Args:
            reddit_client_id: Reddit app client ID
            reddit_client_secret: Reddit app client secret
            reddit_user_agent: User agent string
            gemini_api_key: Google Gemini API key
        """
        self.reddit = self._initialize_reddit(reddit_client_id, reddit_client_secret, reddit_user_agent)
        self._initialize_gemini(gemini_api_key)
        
    def _initialize_reddit(self, client_id: str, client_secret: str, user_agent: str) -> praw.Reddit:
        """Initialize Reddit API client"""
        # Try environment variables first, then parameters
        client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = user_agent or os.getenv('REDDIT_USER_AGENT', 'PersonaGenerator/1.0')
        
        if not client_id or not client_secret:
            raise ValueError("Reddit credentials not provided. Use setup_credentials() or pass them as parameters.")
        
        return praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            timeout=60
        )
    
    def _initialize_gemini(self, api_key: str):
        """Initialize Gemini API client"""
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("Gemini API key not provided. Use setup_credentials() or pass it as parameter.")
        
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    def extract_username_from_url(self, url: str) -> str:
        """Extract username from Reddit profile URL"""
        patterns = [
            r'reddit\.com/u/([^/]+)',
            r'reddit\.com/user/([^/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract username from URL: {url}")
    
    def scrape_user_data(self, username: str, limit: int = 100) -> Dict:
        """Scrape user's posts and comments"""
        try:
            user = self.reddit.redditor(username)
            
            # Get user info
            user_info = {
                'username': username,
                'created_utc': user.created_utc,
                'comment_karma': user.comment_karma,
                'link_karma': user.link_karma,
                'total_karma': user.comment_karma + user.link_karma,
                'account_age_days': (datetime.now().timestamp() - user.created_utc) / 86400,
                'posts': [],
                'comments': []
            }
            
            # Scrape posts
            print(f"🔍 Scraping posts for u/{username}...")
            for submission in user.submissions.new(limit=limit):
                post_data = {
                    'title': submission.title,
                    'content': submission.selftext,
                    'url': f"https://reddit.com{submission.permalink}",
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'created_utc': submission.created_utc,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments
                }
                user_info['posts'].append(post_data)
            
            # Scrape comments
            print(f"💬 Scraping comments for u/{username}...")
            for comment in user.comments.new(limit=limit):
                comment_data = {
                    'content': comment.body,
                    'url': f"https://reddit.com{comment.permalink}",
                    'subreddit': comment.subreddit.display_name,
                    'score': comment.score,
                    'created_utc': comment.created_utc,
                    'parent_id': comment.parent_id
                }
                user_info['comments'].append(comment_data)
            
            print(f"✓ Found {len(user_info['posts'])} posts and {len(user_info['comments'])} comments")
            return user_info
            
        except Exception as e:
            print(f"❌ Error scraping user data: {e}")
            return None
    
    def analyze_with_gemini(self, user_data: Dict) -> Dict:
        """Use Gemini AI to analyze user data and extract persona characteristics"""
        
        # Prepare content for analysis
        posts_text = "\n".join([f"POST: {post['title']} - {post['content']}" 
                               for post in user_data['posts'] if post['content']])
        comments_text = "\n".join([f"COMMENT: {comment['content']}" 
                                  for comment in user_data['comments']])
        
        # Prepare subreddit activity
        subreddit_activity = {}
        for post in user_data['posts']:
            subreddit_activity[post['subreddit']] = subreddit_activity.get(post['subreddit'], 0) + 1
        for comment in user_data['comments']:
            subreddit_activity[comment['subreddit']] = subreddit_activity.get(comment['subreddit'], 0) + 1
        
        top_subreddits = sorted(subreddit_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        prompt = f"""
        Analyze this Reddit user's profile and create a detailed user persona. Based on their posts and comments, extract the following characteristics:

        USER DATA:
        Username: {user_data['username']}
        Account Age: {user_data['account_age_days']:.0f} days
        Total Karma: {user_data['total_karma']}
        Posts: {len(user_data['posts'])}
        Comments: {len(user_data['comments'])}
        Top Subreddits: {top_subreddits}

        POSTS:
        {posts_text[:4000]}

        COMMENTS:
        {comments_text[:4000]}

        Please analyze and provide a JSON response with the following structure. For each characteristic, provide the inferred value and cite specific posts/comments that support your inference. Use actual quotes from the user's content:

        {{
            "estimated_age": {{
                "value": "Age range or specific age based on content",
                "reasoning": "Explanation of how you determined this",
                "evidence": ["Direct quote from post/comment that supports this inference"]
            }},
            "occupation": {{
                "value": "Job title or field or 'Unknown' if not clear",
                "reasoning": "Explanation based on content analysis",
                "evidence": ["Supporting quotes from posts/comments"]
            }},
            "location": {{
                "value": "City, Country or region or 'Unknown' if not mentioned",
                "reasoning": "Explanation",
                "evidence": ["Supporting quotes"]
            }},
            "relationship_status": {{
                "value": "Single/Married/In a relationship/Unknown",
                "reasoning": "Explanation",
                "evidence": ["Supporting quotes"]
            }},
            "personality_type": {{
                "value": "Personality traits and type description",
                "reasoning": "Explanation based on communication patterns",
                "evidence": ["Supporting quotes showing personality"]
            }},
            "interests": {{
                "value": "List of main interests and hobbies",
                "reasoning": "Based on subreddit activity and content",
                "evidence": ["Supporting quotes"]
            }},
            "values": {{
                "value": "Core values and beliefs",
                "reasoning": "Explanation",
                "evidence": ["Supporting quotes"]
            }},
            "communication_style": {{
                "value": "How they communicate online",
                "reasoning": "Analysis of their writing style",
                "evidence": ["Supporting quotes"]
            }},
            "online_behavior": {{
                "value": "Online behavior patterns",
                "reasoning": "Based on activity patterns",
                "evidence": ["Supporting quotes"]
            }},
            "activity_patterns": {{
                "value": "When and how they use Reddit",
                "reasoning": "Analysis of posting patterns",
                "evidence": ["Supporting quotes"]
            }},
            "primary_motivations": {{
                "value": "What drives them",
                "reasoning": "Explanation",
                "evidence": ["Supporting quotes"]
            }},
            "frustrations": {{
                "value": "Common frustrations and pain points",
                "reasoning": "Based on complaints and issues mentioned",
                "evidence": ["Supporting quotes"]
            }},
            "goals": {{
                "value": "Apparent goals and aspirations",
                "reasoning": "Explanation",
                "evidence": ["Supporting quotes"]
            }},
            "tech_savviness": {{
                "value": "Technical skill level assessment",
                "reasoning": "Based on technical discussions",
                "evidence": ["Supporting quotes"]
            }},
            "preferred_platforms": {{
                "value": "Preferred platforms and tools",
                "reasoning": "Based on mentions and usage",
                "evidence": ["Supporting quotes"]
            }},
            "representative_quote": {{
                "value": "A quote that best represents their personality",
                "reasoning": "Why this quote is representative",
                "evidence": ["The actual quote from their content"]
            }}
        }}

        IMPORTANT: 
        - Use ONLY actual quotes from the user's posts and comments as evidence
        - If information is not available or unclear, state "Unknown" for the value
        - Be specific and cite real content, not generic statements
        - Focus on what can be reasonably inferred from the available content
        - Ensure all evidence quotes are actual text from the user's content
        """
        
        try:
            print("🤖 Analyzing with Gemini AI...")
            response = self.gemini_model.generate_content(prompt)
            
            # Clean up the response text to extract JSON
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Parse JSON response
            ai_analysis = json.loads(response_text)
            print("✓ AI analysis completed")
            return ai_analysis
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing AI response as JSON: {e}")
            print("Raw response:", response.text[:500])
            return None
        except Exception as e:
            print(f"❌ Error with Gemini analysis: {e}")
            return None
    
    def create_citations(self, evidence_quotes: List[str], user_data: Dict) -> List[Citation]:
        """Create Citation objects from evidence quotes"""
        citations = []
        
        for quote in evidence_quotes:
            # Find the quote in posts or comments
            citation = self._find_quote_source(quote, user_data)
            if citation:
                citations.append(citation)
        
        return citations
    
    def _find_quote_source(self, quote: str, user_data: Dict) -> Optional[Citation]:
        """Find the source of a quote in user data"""
        # Clean the quote for matching
        clean_quote = quote.strip().lower()
        
        # Search in posts
        for post in user_data['posts']:
            if clean_quote in post['content'].lower() or clean_quote in post['title'].lower():
                return Citation(
                    content=quote,
                    post_type='post',
                    url=post['url'],
                    created_utc=post['created_utc'],
                    subreddit=post['subreddit'],
                    score=post['score']
                )
        
        # Search in comments
        for comment in user_data['comments']:
            if clean_quote in comment['content'].lower():
                return Citation(
                    content=quote,
                    post_type='comment',
                    url=comment['url'],
                    created_utc=comment['created_utc'],
                    subreddit=comment['subreddit'],
                    score=comment['score']
                )
        
        # If not found, create a generic citation
        return Citation(
            content=quote,
            post_type='unknown',
            url='',
            created_utc=0,
            subreddit='unknown',
            score=0
        )
    
    def create_persona(self, user_data: Dict, ai_analysis: Dict) -> UserPersona:
        """Create a UserPersona object from analyzed data"""
        
        def create_characteristic(key: str) -> PersonaCharacteristic:
            analysis = ai_analysis.get(key, {})
            citations = self.create_citations(analysis.get('evidence', []), user_data)
            return PersonaCharacteristic(
                value=analysis.get('value', 'Unknown'),
                citations=citations
            )
        
        return UserPersona(
            estimated_age=create_characteristic('estimated_age'),
            occupation=create_characteristic('occupation'),
            location=create_characteristic('location'),
            relationship_status=create_characteristic('relationship_status'),
            personality_type=create_characteristic('personality_type'),
            interests=create_characteristic('interests'),
            values=create_characteristic('values'),
            communication_style=create_characteristic('communication_style'),
            online_behavior=create_characteristic('online_behavior'),
            activity_patterns=create_characteristic('activity_patterns'),
            primary_motivations=create_characteristic('primary_motivations'),
            frustrations=create_characteristic('frustrations'),
            goals=create_characteristic('goals'),
            tech_savviness=create_characteristic('tech_savviness'),
            preferred_platforms=create_characteristic('preferred_platforms'),
            representative_quote=create_characteristic('representative_quote'),
            username=user_data['username'],
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            total_posts=len(user_data['posts']),
            total_comments=len(user_data['comments']),
            account_age_days=int(user_data['account_age_days']),
            karma=user_data['total_karma']
        )
    
    def format_persona_report(self, persona: UserPersona) -> str:
        """Format the persona into a readable report"""
        
        def format_characteristic(name: str, char: PersonaCharacteristic) -> str:
            result = f"\n{name.upper().replace('_', ' ')}: {char.value}\n"
            if char.citations:
                result += "Citations:\n"
                for i, citation in enumerate(char.citations, 1):
                    result += f"  {i}. [{citation.post_type.upper()}] {citation.content[:100]}...\n"
                    if citation.url:
                        result += f"     Source: {citation.url}\n"
                    result += f"     Subreddit: r/{citation.subreddit} | Score: {citation.score}\n\n"
            return result
        
        report = f"""
================================================================================
                        REDDIT USER PERSONA REPORT
================================================================================

USERNAME: u/{persona.username}
ANALYSIS DATE: {persona.analysis_date}
ACCOUNT AGE: {persona.account_age_days} days
TOTAL POSTS: {persona.total_posts}
TOTAL COMMENTS: {persona.total_comments}
KARMA: {persona.karma}

================================================================================
                            PERSONA OVERVIEW
================================================================================
{format_characteristic('Representative Quote', persona.representative_quote)}

================================================================================
                            DEMOGRAPHICS
================================================================================
{format_characteristic('Estimated Age', persona.estimated_age)}
{format_characteristic('Occupation', persona.occupation)}
{format_characteristic('Location', persona.location)}
{format_characteristic('Relationship Status', persona.relationship_status)}

================================================================================
                            PERSONALITY & VALUES
================================================================================
{format_characteristic('Personality Type', persona.personality_type)}
{format_characteristic('Interests', persona.interests)}
{format_characteristic('Values', persona.values)}

================================================================================
                            BEHAVIORAL PATTERNS
================================================================================
{format_characteristic('Communication Style', persona.communication_style)}
{format_characteristic('Online Behavior', persona.online_behavior)}
{format_characteristic('Activity Patterns', persona.activity_patterns)}

================================================================================
                            MOTIVATIONS & GOALS
================================================================================
{format_characteristic('Primary Motivations', persona.primary_motivations)}
{format_characteristic('Frustrations', persona.frustrations)}
{format_characteristic('Goals', persona.goals)}

================================================================================
                            TECHNICAL PROFILE
================================================================================
{format_characteristic('Tech Savviness', persona.tech_savviness)}
{format_characteristic('Preferred Platforms', persona.preferred_platforms)}

================================================================================
                            END OF REPORT
================================================================================
"""
        return report
    
    def save_persona_to_file(self, persona: UserPersona, filename: str = None):
        """Save persona report to a text file"""
        if filename is None:
            filename = f"persona_{persona.username}_{persona.analysis_date}.txt"
        
        report = self.format_persona_report(persona)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"💾 Persona report saved to: {filename}")
    
    def generate_persona_from_url(self, profile_url: str, limit: int = 100) -> UserPersona:
        """Main method to generate persona from Reddit profile URL"""
        try:
            # Extract username from URL
            username = self.extract_username_from_url(profile_url)
            print(f"👤 Analyzing user: u/{username}")
            
            # Scrape user data
            user_data = self.scrape_user_data(username, limit)
            if not user_data:
                raise Exception("Failed to scrape user data")
            
            # Analyze with AI
            ai_analysis = self.analyze_with_gemini(user_data)
            if not ai_analysis:
                raise Exception("Failed to analyze with AI")
            
            # Create persona
            persona = self.create_persona(user_data, ai_analysis)
            
            # Save to file
            self.save_persona_to_file(persona)
            
            return persona
            
        except Exception as e:
            print(f"❌ Error generating persona: {e}")
            return None


def setup_credentials():
    """Interactive setup for API credentials"""
    print("🔐 Setting up API credentials")
    print("=" * 50)
    
    # Reddit credentials
    print("\n1. Reddit API Setup:")
    print("   - Go to https://www.reddit.com/prefs/apps")
    print("   - Create a new app (choose 'script' type)")
    print("   - Note your Client ID and Client Secret")
    
    reddit_client_id = input("\nEnter Reddit Client ID: ").strip()
    reddit_client_secret = input("Enter Reddit Client Secret: ").strip()
    reddit_user_agent = input("Enter Reddit User Agent (or press Enter for default): ").strip()
    if not reddit_user_agent:
        reddit_user_agent = "PersonaGenerator/1.0"
    
    # Gemini credentials
    print("\n2. Gemini API Setup:")
    print("   - Go to https://makersuite.google.com/app/apikey")
    print("   - Create a new API key")
    
    gemini_api_key = input("\nEnter Gemini API Key: ").strip()
    
    # Store in environment variables for current session
    os.environ['REDDIT_CLIENT_ID'] = reddit_client_id
    os.environ['REDDIT_CLIENT_SECRET'] = reddit_client_secret
    os.environ['REDDIT_USER_AGENT'] = reddit_user_agent
    os.environ['GEMINI_API_KEY'] = gemini_api_key
    
    print("\n✅ Credentials configured for current session!")
    return reddit_client_id, reddit_client_secret, reddit_user_agent, gemini_api_key

def quick_setup(reddit_client_id: str, reddit_client_secret: str, gemini_api_key: str, 
                reddit_user_agent: str = "PersonaGenerator/1.0"):
    """Quick setup with provided credentials"""
    os.environ['REDDIT_CLIENT_ID'] = reddit_client_id
    os.environ['REDDIT_CLIENT_SECRET'] = reddit_client_secret
    os.environ['REDDIT_USER_AGENT'] = reddit_user_agent
    os.environ['GEMINI_API_KEY'] = gemini_api_key
    print("✅ Credentials configured!")

def generate_persona(profile_url: str, limit: int = 100):
    """Main function to generate persona - simplified for notebook use"""
    try:
        generator = RedditUserPersonaGenerator()
        persona = generator.generate_persona_from_url(profile_url, limit)
        
        if persona:
            print(f"\n🎉 Persona generated successfully for u/{persona.username}!")
            print(f"📄 Report saved to: persona_{persona.username}_{persona.analysis_date}.txt")
            
            # Display summary
            print(f"\n📊 Summary:")
            print(f"   Age: {persona.estimated_age.value}")
            print(f"   Occupation: {persona.occupation.value}")
            print(f"   Location: {persona.location.value}")
            print(f"   Interests: {persona.interests.value}")
            print(f"   Quote: {persona.representative_quote.value}")
            
            return persona
        else:
            print("❌ Failed to generate persona")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None



# In[65]:


setup_credentials()


# In[69]:


sample_users = [
    "https://www.reddit.com/user/kojied/",
    "https://www.reddit.com/user/Hungry-Move-6603/"
]

for i, user_url in enumerate(sample_users, 1):
    print(f"\n[{i}/{len(sample_users)}] Analyzing: {user_url}")
    try:
        persona = generate_persona(user_url)
        if persona:
            print(f"✅ Completed: u/{persona.username}")
        else:
            print(f"❌ Failed: {user_url}")
    except Exception as e:
        print(f"❌ Error with {user_url}: {e}")

print("\n🏁 Sample generation completed!")


# In[71]:


custom_url = input("Enter a Reddit profile URL to analyze: ")
if custom_url:
    persona = generate_persona(custom_url)
    if persona:
        print(f"✅ Analysis complete for u/{persona.username}")
    else:
        print("❌ Analysis failed")


# In[77]:


import os
txt_files = [f for f in os.listdir('.') if f.startswith('persona_') and f.endswith('.txt')]
print("📁 Generated persona files:")
for file in txt_files:
    print(f"  - {file}")


# In[ ]:




